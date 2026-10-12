"""Target-leakage column names. Never used as model inputs."""

from __future__ import annotations

from typing import Iterable

# Verified from data/z_alizadeh_sani_extension.xlsx:
# vessel labels LAD/LCX/RCA (Stenotic/Normal) and overall angiography Cath (CAD/Normal).
# There is no separate CAD column. Include common aliases so accidental CAD-derived
# fields still fail loudly.
LEAKAGE_COLUMNS = (
    "LAD",
    "LCX",
    "RCA",
    "Cath",
    "CAD",
    "lad",
    "lcx",
    "rca",
    "cath",
    "cad",
)


def clean_column_name(name: str) -> str:
    return (
        str(name)
        .strip()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(".", "_")
    )


def _norm(name: str) -> str:
    return clean_column_name(name).lower()


def leakage_name_set() -> set[str]:
    return {_norm(col) for col in LEAKAGE_COLUMNS}


def assert_no_leakage(feature_columns: Iterable[str]) -> None:
    overlap = {_norm(col) for col in feature_columns} & leakage_name_set()
    if overlap:
        raise AssertionError(f"Leakage columns present in features: {sorted(overlap)}")
