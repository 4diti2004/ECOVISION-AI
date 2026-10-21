"""Validate a trained YOLO waste detector against the validation split."""

from __future__ import annotations

import argparse
from pathlib import Path

from ml.train import DEFAULT_DATA_CONFIG, load_data_config


def validate_model(model_path: Path, data_path: Path) -> None:
    """Run Ultralytics validation and print its metrics."""
    if not model_path.is_file():
        raise FileNotFoundError(
            f"Model was not found: {model_path}. Train it with ml\\train.py first."
        )
    load_data_config(data_path)

    try:
        from ultralytics import YOLO
    except ImportError as error:
        raise RuntimeError(
            "Ultralytics is not installed. Run: "
            "python -m pip install -r backend\\requirements.txt"
        ) from error

    metrics = YOLO(str(model_path)).val(data=str(data_path))
    print(f"Validation completed for: {model_path}")
    print(f"mAP50-95: {metrics.box.map:.4f}")
    print(f"mAP50: {metrics.box.map50:.4f}")


def main() -> None:
    """Parse validation options and validate the trained model."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        type=Path,
        default=Path(__file__).with_name("models") / "waste_detector.pt",
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_CONFIG)
    args = parser.parse_args()
    validate_model(args.model.resolve(), args.data.resolve())


if __name__ == "__main__":
    main()
