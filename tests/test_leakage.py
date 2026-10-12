from ml.leakage import LEAKAGE_COLUMNS, assert_no_leakage
from ml.preprocess import prepare


def test_leakage_constant_includes_vessels_and_cath():
    names = {c.lower() for c in LEAKAGE_COLUMNS}
    for col in ("lad", "lcx", "rca", "cath"):
        assert col in names


def test_assert_no_leakage_fails_loudly():
    try:
        assert_no_leakage(["Age", "LAD", "BMI"])
    except AssertionError as exc:
        assert "lad" in str(exc).lower()
    else:
        raise AssertionError("Leakage assertion did not fire")


def test_prepared_features_exclude_targets():
    bundle = prepare()
    cols = {c.lower() for c in bundle["X"].columns}
    for leak in ("lad", "lcx", "rca", "cath", "cad"):
        assert leak not in cols
    assert_no_leakage(bundle["X"].columns)
    for target in ("cad", "lad", "lcx", "rca"):
        assert target in bundle["y"].columns
