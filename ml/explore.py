"""Inspect the real dataset and write docs/data_summary.md."""

from __future__ import annotations

from pathlib import Path

from ml.preprocess import load_raw, prepare

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    raw = load_raw()
    bundle = prepare()
    y = bundle["y"]
    X = bundle["X"]
    lines = [
        "# Dataset summary",
        "",
        "Source file: `data/z_alizadeh_sani_extension.xlsx` (UCI extention of Z-Alizadeh sani, id=411).",
        "",
        f"- Rows: **{raw.shape[0]}**",
        f"- Raw columns: **{raw.shape[1]}**",
        f"- Missing cells (raw): **{int(raw.isna().sum().sum())}**",
        f"- Leakage-safe feature count: **{X.shape[1]}**",
        "",
        "## Targets (encoded 1 = disease / stenotic)",
        "",
        "| Target | Positive | Negative | Prevalence |",
        "| --- | --- | --- | --- |",
    ]
    for col in y.columns:
        pos = int(y[col].sum())
        neg = int((1 - y[col]).sum())
        lines.append(f"| {col.upper()} | {pos} | {neg} | {pos / len(y):.3f} |")

    lines += [
        "",
        "## Raw columns and dtypes",
        "",
        "| Column | dtype | nunique | missing | sample values |",
        "| --- | --- | --- | --- | --- |",
    ]
    for col in raw.columns:
        samples = raw[col].dropna().astype(str).unique()[:6]
        sample_txt = ", ".join(samples)
        lines.append(
            f"| {col} | {raw[col].dtype} | {raw[col].nunique(dropna=False)} | {int(raw[col].isna().sum())} | {sample_txt} |"
        )
    lines += [
        "",
        "## Leakage columns (never used as inputs)",
        "",
        "LAD, LCX, RCA (Stenotic/Normal) and Cath (CAD/Normal). No separate CAD column exists in this file.",
        "Cath is the overall CAD status target.",
        "",
        "## Notes",
        "",
        "- `Exertional_CP` is constant (`N`) and is dropped.",
        "- `Sex` uses dataset spelling `Fmale` / `Male`.",
        "- `Region_RWMA` is an integer 0–4 echo finding, not a 3D lesion map.",
        "- Diastolic BP is absent; pulse pressure was not engineered.",
        "",
    ]
    out = ROOT / "docs" / "data_summary.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
