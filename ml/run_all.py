"""Retrain from scratch: explore -> preprocess -> train."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.explore import main as explore_main
from ml.preprocess import main as preprocess_main
from ml.train import main as train_main


def main() -> None:
    explore_main()
    preprocess_main()
    train_main()


if __name__ == "__main__":
    main()
