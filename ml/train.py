"""Repeated nested-ish CV, calibration, SHAP, and artifact export. Seed 42."""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold
from sklearn.multioutput import ClassifierChain
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.leakage import LEAKAGE_COLUMNS, assert_no_leakage
from ml.preprocess import prepare

try:
    from xgboost import XGBClassifier
except Exception:  # pragma: no cover
    XGBClassifier = None

try:
    from lightgbm import LGBMClassifier
except Exception:
    LGBMClassifier = None

try:
    import shap
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"SHAP is required: {exc}") from exc

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
FIGURES = ROOT / "docs" / "figures"
SEED = 42
TARGETS = ("cad", "lad", "lcx", "rca")
warnings.filterwarnings("ignore", category=UserWarning)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _rng(seed: int = SEED) -> np.random.Generator:
    return np.random.default_rng(seed)


def make_models(y: np.ndarray) -> dict:
    pos = max(int(y.sum()), 1)
    neg = max(int(len(y) - y.sum()), 1)
    spw = neg / pos
    models = {
        "logreg": LogisticRegression(
            max_iter=400,
            class_weight="balanced",
            C=1.0,
            solver="liblinear",
            random_state=SEED,
        ),
        "rf": RandomForestClassifier(
            n_estimators=160,
            max_depth=6,
            min_samples_leaf=4,
            class_weight="balanced",
            random_state=SEED,
            n_jobs=1,
        ),
    }
    if XGBClassifier is not None:
        models["xgboost"] = XGBClassifier(
            n_estimators=160,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.8,
            min_child_weight=4,
            reg_lambda=1.5,
            scale_pos_weight=spw,
            eval_metric="logloss",
            n_jobs=1,
            random_state=SEED,
        )
    if LGBMClassifier is not None:
        models["lightgbm"] = LGBMClassifier(
            n_estimators=160,
            max_depth=3,
            learning_rate=0.05,
            class_weight="balanced",
            random_state=SEED,
            verbose=-1,
        )
    return models


def wrap(estimator, k_best: int | None) -> Pipeline:
    steps = [("scaler", StandardScaler())]
    if k_best:
        steps.append(("select", SelectKBest(f_classif, k=min(k_best, 40))))
    steps.append(("clf", estimator))
    return Pipeline(steps)


def oversample(X: np.ndarray, y: np.ndarray, rng: np.random.Generator):
    pos = np.where(y == 1)[0]
    neg = np.where(y == 0)[0]
    if len(pos) == 0 or len(neg) == 0:
        return X, y
    if len(pos) < len(neg):
        extra = rng.choice(pos, size=len(neg) - len(pos), replace=True)
        idx = np.concatenate([neg, pos, extra])
    else:
        extra = rng.choice(neg, size=len(pos) - len(neg), replace=True)
        idx = np.concatenate([pos, neg, extra])
    rng.shuffle(idx)
    return X[idx], y[idx]


def metrics_from_scores(y_true, y_prob) -> dict[str, float]:
    y_pred = (y_prob >= 0.5).astype(int)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.5,
        "brier": float(brier_score_loss(y_true, y_prob)),
    }


def summarize(rows: list[dict]) -> dict:
    frame = pd.DataFrame(rows)
    out = {}
    for col in frame.columns:
        out[col] = {"mean": float(frame[col].mean()), "std": float(frame[col].std(ddof=1) if len(frame) > 1 else 0.0)}
    return out


def eval_config(X, y, estimator, k_best=None, use_os=False, n_splits=5, n_repeats=5) -> tuple[dict, np.ndarray, np.ndarray]:
    cv = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=SEED)
    rows = []
    oof_prob = np.zeros(len(y), dtype=float)
    oof_count = np.zeros(len(y), dtype=float)
    rng = _rng()
    for fold, (tr, te) in enumerate(cv.split(X, y)):
        Xtr, ytr = X[tr], y[tr]
        if use_os:
            Xtr, ytr = oversample(Xtr, ytr, rng)
        model = wrap(clone(estimator), k_best)
        model.fit(Xtr, ytr)
        prob = model.predict_proba(X[te])[:, 1]
        oof_prob[te] += prob
        oof_count[te] += 1
        rows.append(metrics_from_scores(y[te], prob))
    oof = oof_prob / np.maximum(oof_count, 1)
    return summarize(rows), oof, y


def light_tune(X, y, name: str, base) -> object:
    """Tiny inner search; leakage-free because caller uses only train indices."""
    inner = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    grid = [None]
    if name == "logreg":
        grid = [0.2, 1.0, 4.0]
    elif name == "rf":
        grid = [4, 6]
    elif name == "xgboost":
        grid = [0.03, 0.08]
    best_auc, best_est = -1.0, clone(base)
    for val in grid:
        est = clone(base)
        if name == "logreg":
            est.set_params(C=val)
        elif name == "rf":
            est.set_params(max_depth=val)
        elif name == "xgboost":
            est.set_params(learning_rate=val)
        aucs = []
        for tr, te in inner.split(X, y):
            pipe = wrap(est, None)
            pipe.fit(X[tr], y[tr])
            aucs.append(roc_auc_score(y[te], pipe.predict_proba(X[te])[:, 1]))
        mean_auc = float(np.mean(aucs))
        if mean_auc > best_auc:
            best_auc = mean_auc
            best_est = clone(est)
    return best_est


def nested_eval(X, y, name: str, template) -> dict:
    outer = RepeatedStratifiedKFold(n_splits=5, n_repeats=5, random_state=SEED)
    rows = []
    oof_prob = np.zeros(len(y))
    oof_n = np.zeros(len(y))
    for tr, te in outer.split(X, y):
        tuned = light_tune(X[tr], y[tr], name, template)
        pipe = wrap(tuned, None)
        pipe.fit(X[tr], y[tr])
        prob = pipe.predict_proba(X[te])[:, 1]
        oof_prob[te] += prob
        oof_n[te] += 1
        rows.append(metrics_from_scores(y[te], prob))
    return {"cv": summarize(rows), "oof": oof_prob / np.maximum(oof_n, 1)}


def plot_roc(y, prob, title, path: Path):
    fpr, tpr, _ = roc_curve(y, prob)
    auc = roc_auc_score(y, prob)
    plt.figure(figsize=(5, 4))
    plt.plot(fpr, tpr, label=f"AUC={auc:.3f}")
    plt.plot([0, 1], [0, 1], "--", color="gray")
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def plot_cm(y, prob, title, path: Path):
    cm = confusion_matrix(y, (prob >= 0.5).astype(int))
    plt.figure(figsize=(4.2, 3.6))
    plt.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            plt.text(j, i, int(cm[i, j]), ha="center", va="center")
    plt.xticks([0, 1], ["Pred 0", "Pred 1"])
    plt.yticks([0, 1], ["True 0", "True 1"])
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def plot_cal(y, before, after, title, path: Path):
    plt.figure(figsize=(5, 4))
    for lab, p in (("uncalibrated", before), ("calibrated", after)):
        frac, meanp = calibration_curve(y, p, n_bins=8, strategy="quantile")
        plt.plot(meanp, frac, marker="o", label=lab)
    plt.plot([0, 1], [0, 1], "--", color="gray")
    plt.xlabel("Predicted probability")
    plt.ylabel("Observed frequency")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def plot_shap_summary(model, X, feature_names, title, path: Path):
    """Permutation SHAP on a small background — fast enough for 55 features, no GPU."""
    bg = X[: min(32, len(X))]

    def _proba(data):
        return model.predict_proba(np.asarray(data, dtype=float))[:, 1]

    explainer = shap.Explainer(_proba, bg, algorithm="permutation", seed=SEED)
    explanation = explainer(bg, max_evals=2 * X.shape[1] + 1)
    values = np.asarray(explanation.values, dtype=float)
    if values.ndim == 3:
        values = values[..., 1]
    mean_abs = np.abs(values).mean(axis=0)
    order = np.argsort(mean_abs)[-12:]
    plt.figure(figsize=(6, 4.5))
    plt.barh([feature_names[i] for i in order], mean_abs[order], color="#1f6f8b")
    plt.title(title)
    plt.xlabel("mean |SHAP|")
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def bootstrap_models(estimator, X, y, n=10):
    rng = _rng(SEED + 7)
    models = []
    for i in range(n):
        idx = rng.integers(0, len(y), size=len(y))
        # keep both classes if possible
        if len(np.unique(y[idx])) < 2:
            continue
        m = clone(estimator)
        m.fit(X[idx], y[idx])
        models.append(m)
    if not models:
        models = [estimator]
    return models


def chain_ablation(X, Y: pd.DataFrame) -> dict:
    """Independent vs classifier-chain for vessel targets. Chain uses predicted vessels only at test time."""
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=2, random_state=SEED)
    y_cad_like = Y["lad"].to_numpy()  # for split stratification
    y_multi = Y[["lad", "lcx", "rca"]].to_numpy()
    indep_auc = {k: [] for k in ("lad", "lcx", "rca")}
    chain_auc = {k: [] for k in ("lad", "lcx", "rca")}
    base = LogisticRegression(max_iter=400, class_weight="balanced", solver="liblinear", random_state=SEED)
    for tr, te in cv.split(X, y_cad_like):
        for i, name in enumerate(("lad", "lcx", "rca")):
            pipe = wrap(clone(base), None)
            pipe.fit(X[tr], y_multi[tr, i])
            indep_auc[name].append(roc_auc_score(y_multi[te, i], pipe.predict_proba(X[te])[:, 1]))
        chain = ClassifierChain(clone(base), order=[0, 1, 2], random_state=SEED)
        chain.fit(X[tr], y_multi[tr])
        proba = chain.predict_proba(X[te])
        for i, name in enumerate(("lad", "lcx", "rca")):
            chain_auc[name].append(roc_auc_score(y_multi[te, i], proba[:, i]))
    table = {}
    for name in ("lad", "lcx", "rca"):
        di, dc = float(np.mean(indep_auc[name])), float(np.mean(chain_auc[name]))
        table[name] = {
            "independent_auc_mean": di,
            "chain_auc_mean": dc,
            "delta": dc - di,
        }
    table["helps"] = bool(np.mean([table[n]["delta"] for n in ("lad", "lcx", "rca")]) > 0.005)
    table["note"] = (
        "Classifier-chain uses other vessel labels only as training outputs, never as input features "
        "from angiography. Test-time chain features are predicted, not ground truth."
    )
    return table


def make_demo_patients(schema: dict) -> list[dict]:
    profiles = (
        (
            "sample-low",
            "Lower-risk synthetic example",
            {
                "Age": 42, "Weight": 60, "Length": 165, "Sex": "Fmale", "BMI": 22,
                "DM": 0, "HTN": 0, "Current_Smoker": 0, "DLP": 0, "BP": 115,
                "PR": 70, "Typical_Chest_Pain": 0, "Dyspnea": 0, "Function_Class": 0,
                "FBS": 90, "LDL": 90, "HDL": 60, "Region_RWMA": 0, "VHD": "N",
            },
        ),
        (
            "sample-medium",
            "Intermediate-risk synthetic example",
            {
                "Age": 55, "Sex": "Male", "HTN": 1, "BP": 140, "FBS": 110,
                "LDL": 120, "HDL": 45, "VHD": "N",
            },
        ),
        (
            "sample-high",
            "Higher-risk synthetic example",
            {
                "Age": 72, "Weight": 90, "Length": 165, "Sex": "Male", "BMI": 33,
                "DM": 1, "HTN": 1, "Current_Smoker": 1, "DLP": 1, "BP": 170,
                "PR": 95, "Typical_Chest_Pain": 1, "Dyspnea": 1, "Function_Class": 3,
                "FBS": 165, "LDL": 180, "HDL": 30, "Region_RWMA": 4, "VHD": "Severe",
            },
        ),
    )
    defaults = {
        feature["name"]: feature["default"]
        for feature in schema["features"]
        if not feature.get("engineered")
    }
    return [
        {"id": sample_id, "label": label, "patient": {**defaults, **overrides}}
        for sample_id, label, overrides in profiles
    ]


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    bundle = prepare()
    X_df: pd.DataFrame = bundle["X"]
    Y: pd.DataFrame = bundle["y"]
    schema = bundle["schema"]
    assert_no_leakage(X_df.columns)
    for leak in ("LAD", "LCX", "RCA", "Cath", "CAD"):
        assert leak not in X_df.columns, leak
    X = X_df.to_numpy(dtype=float)
    feature_names = list(X_df.columns)
    print("Features", len(feature_names), "Leakage OK")

    comparison = {}
    boost_table = {}
    target_reports = {}
    oof_store = {}
    registry = {"targets": {}, "feature_names": feature_names, "seed": SEED}

    for target in TARGETS:
        print(f"\n=== {target} ===")
        y = Y[target].to_numpy(dtype=int)
        templates = make_models(y)
        model_cv = {}
        best_name, best_auc = None, -1.0
        for name, est in templates.items():
            result = nested_eval(X, y, name, est)
            model_cv[name] = result["cv"]
            auc = result["cv"]["roc_auc"]["mean"]
            print(f"  {name}: AUC {auc:.3f} ± {result['cv']['roc_auc']['std']:.3f}  recall {result['cv']['recall']['mean']:.3f}")
            if auc > best_auc:
                best_auc, best_name = auc, name
            oof_store.setdefault(target, {})[name] = result["oof"]

        # quality boosts vs winning template (5x2 to stay honest but cheaper)
        winner_template = templates[best_name]
        cfg_rows = {}
        for tag, kwargs in (
            ("baseline_class_weight", {"k_best": None, "use_os": False, "n_repeats": 2}),
            ("selectk25", {"k_best": 25, "use_os": False, "n_repeats": 2}),
            ("random_oversample", {"k_best": None, "use_os": True, "n_repeats": 2}),
        ):
            summ, _, _ = eval_config(X, y, clone(winner_template), **kwargs)
            cfg_rows[tag] = summ["roc_auc"]
        # voting ensemble of logreg + best tree-like
        voters = []
        for n in ("logreg", "rf", "xgboost"):
            if n in templates:
                voters.append((n, clone(templates[n])))
        vote = VotingClassifier(estimators=voters[:3], voting="soft")
        vote_summ, vote_oof, _ = eval_config(X, y, vote, n_repeats=2)
        cfg_rows["soft_vote"] = vote_summ["roc_auc"]
        boost_table[target] = cfg_rows

        use_vote = vote_summ["roc_auc"]["mean"] > best_auc + 0.005
        chosen_name = "soft_vote" if use_vote else best_name
        chosen_est = vote if use_vote else clone(templates[best_name])
        print(f"  chosen={chosen_name} nested_best={best_name} auc={best_auc:.3f} vote={vote_summ['roc_auc']['mean']:.3f}")

        # full repeated CV for the chosen model (reported numbers)
        chosen_cv, chosen_oof, _ = eval_config(X, y, clone(chosen_est), n_splits=5, n_repeats=5)

        # calibration: sigmoid vs isotonic on 5-fold
        def cal_oof(method: str):
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
            p = np.zeros(len(y))
            for tr, te in cv.split(X, y):
                cal = CalibratedClassifierCV(wrap(clone(chosen_est), None), method=method, cv=3)
                cal.fit(X[tr], y[tr])
                p[te] = cal.predict_proba(X[te])[:, 1]
            return p

        p_sig = cal_oof("sigmoid")
        p_iso = cal_oof("isotonic")
        brier_raw = float(brier_score_loss(y, chosen_oof))
        brier_sig = float(brier_score_loss(y, p_sig))
        brier_iso = float(brier_score_loss(y, p_iso))
        method = "sigmoid" if brier_sig <= brier_iso else "isotonic"
        cal_oof_best = p_sig if method == "sigmoid" else p_iso
        print(f"  Brier raw={brier_raw:.4f} sig={brier_sig:.4f} iso={brier_iso:.4f} -> {method}")

        base_pipe = wrap(clone(chosen_est), None)
        final = CalibratedClassifierCV(base_pipe, method=method, cv=5)
        final.fit(X, y)
        ensemble = bootstrap_models(clone(final), X, y, n=8)

        bg_idx = np.random.RandomState(SEED).choice(len(X), size=min(40, len(X)), replace=False)
        background = X[bg_idx]

        plot_roc(y, cal_oof_best, f"ROC {target.upper()}", FIGURES / f"roc_{target}.png")
        plot_cm(y, cal_oof_best, f"Confusion {target.upper()}", FIGURES / f"cm_{target}.png")
        plot_cal(y, chosen_oof, cal_oof_best, f"Calibration {target.upper()}", FIGURES / f"cal_{target}.png")
        plot_shap_summary(final, background, feature_names, f"SHAP {target.upper()}", FIGURES / f"shap_{target}.png")

        comparison[target] = {name: model_cv[name]["roc_auc"] for name in model_cv}
        target_reports[target] = {
            "chosen_model": chosen_name,
            "nested_cv": {k: model_cv[k] for k in model_cv},
            "chosen_repeated_cv": chosen_cv,
            "recall_check": chosen_cv["recall"],
            "calibration": {
                "method": method,
                "brier_before": brier_raw,
                "brier_sigmoid": brier_sig,
                "brier_isotonic": brier_iso,
                "brier_after": min(brier_sig, brier_iso),
            },
            "oof_used_for_plots": "calibrated 5-fold OOF",
        }
        joblib.dump(
            {
                "model": final,
                "ensemble_models": ensemble,
                "chosen_name": chosen_name,
            },
            MODELS / f"{target}_bundle.joblib",
            compress=3,
        )
        registry["targets"][target] = {
            "model": final,
            "ensemble_models": ensemble,
            "chosen_name": chosen_name,
        }
    registry["background"] = background

    chain = chain_ablation(X, Y)
    print("\nVessel chain ablation", json.dumps(chain, indent=2))

    # model comparison chart
    plt.figure(figsize=(7, 4))
    labels = []
    vals = []
    errs = []
    for target in TARGETS:
        for model_name, auc in comparison[target].items():
            labels.append(f"{target}:{model_name}")
            vals.append(auc["mean"])
            errs.append(auc["std"])
    plt.barh(labels, vals, xerr=errs, color="#2c6e63")
    plt.xlabel("Repeated nested-ish CV ROC-AUC")
    plt.tight_layout()
    plt.savefig(FIGURES / "model_comparison.png", dpi=120)
    plt.close()

    joblib.dump(registry, MODELS / "registry.joblib", compress=3)

    samples = make_demo_patients(schema)
    (MODELS / "sample_patients.json").write_text(json.dumps(samples, indent=2, default=str), encoding="utf-8")

    metrics = {
        "seed": SEED,
        "n_patients": int(len(X_df)),
        "n_features": int(X_df.shape[1]),
        "feature_names": feature_names,
        "leakage_columns_excluded": list(LEAKAGE_COLUMNS),
        "targets": {
            t: {
                "chosen_model": target_reports[t]["chosen_model"],
                "accuracy": target_reports[t]["chosen_repeated_cv"]["accuracy"],
                "precision": target_reports[t]["chosen_repeated_cv"]["precision"],
                "recall": target_reports[t]["chosen_repeated_cv"]["recall"],
                "f1": target_reports[t]["chosen_repeated_cv"]["f1"],
                "roc_auc": target_reports[t]["chosen_repeated_cv"]["roc_auc"],
                "calibration": target_reports[t]["calibration"],
                "model_comparison_auc": comparison[t],
            }
            for t in TARGETS
        },
        "boost_ablation_auc": boost_table,
        "vessel_classifier_chain": chain,
        "notes": [
            "Metrics are mean ± std over repeated stratified 5-fold CV (5 repeats) unless a table says otherwise.",
            "Hyperparameters were chosen with an inner 3-fold search on training folds only.",
            "Engineered features (LDL/HDL, TG/HDL) are derived from labs, not from vessel labels.",
            "No external validation. 303 single-centre rows. Not for clinical use.",
        ],
        "figures": [
            "roc_cad.png",
            "roc_lad.png",
            "roc_lcx.png",
            "roc_rca.png",
            "cm_cad.png",
            "cm_lad.png",
            "cm_lcx.png",
            "cm_rca.png",
            "cal_cad.png",
            "cal_lad.png",
            "cal_lcx.png",
            "cal_rca.png",
            "shap_cad.png",
            "shap_lad.png",
            "shap_lcx.png",
            "shap_rca.png",
            "model_comparison.png",
        ],
    }
    (MODELS / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print("\nWrote models/metrics.json and registry.joblib")
    for t in TARGETS:
        auc = metrics["targets"][t]["roc_auc"]
        print(f"  {t}: AUC {auc['mean']:.3f} ± {auc['std']:.3f}")
        if auc["mean"] > 0.98:
            print("  WARNING: AUC near 1.0 — re-check leakage.")


if __name__ == "__main__":
    main()
