from __future__ import annotations

from pathlib import Path

from ml.preprocess import load_dataset


def main() -> None:
    frame = load_dataset()
    output_dir = Path("models")
    output_dir.mkdir(exist_ok=True)
    print("Dataset loaded. Full training pipeline is intentionally staged.")
    print("Next implementation step: target mapping, leakage-safe feature matrix, repeated CV, calibration, and SHAP.")
    print(f"Rows available: {len(frame)}")


if __name__ == "__main__":
    main()
