from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


LEAKAGE_COLUMNS = {"Cath", "CAD", "LAD", "LCX", "RCA", "cad", "lad", "lcx", "rca"}


def clean_column_name(name: str) -> str:
    return (
        str(name)
        .strip()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
    )


def assert_no_leakage(feature_columns: Iterable[str]) -> None:
    normalized = {clean_column_name(col).lower() for col in feature_columns}
    leakage = {col.lower() for col in LEAKAGE_COLUMNS}
    overlap = normalized.intersection(leakage)
    if overlap:
        raise AssertionError(f"Leakage columns present in features: {sorted(overlap)}")


def load_dataset(data_dir: str | Path = "data") -> pd.DataFrame:
    data_path = Path(data_dir)
    candidates = sorted(
        [*data_path.glob("*.csv"), *data_path.glob("*.xlsx"), *data_path.glob("*.xls")]
    )
    if not candidates:
        raise FileNotFoundError(
            "No dataset found in data/. Add the Z-Alizadeh Sani extension file first."
        )
    path = candidates[0]
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
    else:
        frame = pd.read_excel(path)
    frame.columns = [clean_column_name(col) for col in frame.columns]
    return frame


def main() -> None:
    frame = load_dataset()
    print(f"Loaded dataset with {frame.shape[0]} rows and {frame.shape[1]} columns.")
    print("Columns:")
    for column in frame.columns:
        print(f"- {column}")


if __name__ == "__main__":
    main()
