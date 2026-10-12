import pytest

from ml.preprocess import prepare, vectorize_patient


def test_schema_covers_feature_names():
    bundle = prepare()
    schema = bundle["schema"]
    names = {item["name"] for item in schema["features"]}
    for feat in schema["feature_names"]:
        assert feat in names
    for item in schema["features"]:
        assert item["group"]
        assert item["label"]
        assert "default" in item


def test_vectorize_patient_matches_training_width():
    bundle = prepare()
    schema = bundle["schema"]
    patient = {item["name"]: item["default"] for item in schema["features"] if not item.get("engineered")}
    X = vectorize_patient(patient, schema)
    assert list(X.columns) == schema["feature_names"]
    assert X.shape == (1, len(schema["feature_names"]))


def test_vectorize_rejects_unknown_and_out_of_range_values():
    bundle = prepare()
    schema = bundle["schema"]
    with pytest.raises(ValueError, match="Unknown patient feature"):
        vectorize_patient({"Age": 60, "unexpected": 1}, schema)
    age = next(feature for feature in schema["features"] if feature["name"] == "Age")
    with pytest.raises(ValueError, match="Age must be at most"):
        vectorize_patient({"Age": age["max"] + 1}, schema)
