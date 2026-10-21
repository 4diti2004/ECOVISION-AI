"""Validate the waste dataset and train a YOLO detection model."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

EXPECTED_CLASSES = [
    "plastic",
    "paper",
    "cardboard",
    "glass",
    "metal",
    "organic",
    "e_waste",
    "other",
]
DEFAULT_DATA_CONFIG = Path(__file__).with_name("data.yaml")
DEFAULT_OUTPUT_DIR = Path(__file__).with_name("models")


def load_data_config(config_path: Path) -> tuple[dict[str, Any], Path]:
    """Load and validate a YOLO data configuration."""
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Dataset configuration was not found: {config_path}. "
            "Run this command from the project root or provide --data."
        )

    with config_path.open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    if not isinstance(config, dict):
        raise ValueError(f"Dataset configuration must be a YAML mapping: {config_path}")

    names = config.get("names")
    if isinstance(names, dict):
        names = [names[index] for index in sorted(names, key=int)]
    if names != EXPECTED_CLASSES:
        raise ValueError(
            f"data.yaml classes must be exactly {EXPECTED_CLASSES}; found {names!r}"
        )

    for key in ("path", "train", "val"):
        if not isinstance(config.get(key), str) or not config[key].strip():
            raise ValueError(f"data.yaml must define a non-empty '{key}' value")

    dataset_root = Path(config["path"])
    if not dataset_root.is_absolute():
        dataset_root = (config_path.parent.parent / dataset_root).resolve()
    return config, dataset_root


def validate_dataset(config_path: Path) -> None:
    """Ensure the configured image and label directories exist."""
    config, dataset_root = load_data_config(config_path)
    missing = []
    for split in ("train", "val"):
        image_dir = dataset_root / config[split]
        label_dir = dataset_root / "labels" / Path(config[split]).name
        if not image_dir.is_dir():
            missing.append(str(image_dir))
        if not label_dir.is_dir():
            missing.append(str(label_dir))

    if missing:
        missing_paths = "\n".join(f"  - {path}" for path in missing)
        raise FileNotFoundError(
            "Dataset folders are missing. Place your YOLO dataset at:\n"
            f"{dataset_root}\nMissing:\n{missing_paths}"
        )


def train_model(
    config_path: Path,
    output_dir: Path,
    model_name: str,
    epochs: int,
    image_size: int,
) -> Path:
    """Train YOLO and copy the best checkpoint to the stable model location."""
    validate_dataset(config_path)

    try:
        from ultralytics import YOLO
    except ImportError as error:
        raise RuntimeError(
            "Ultralytics is not installed. Run: "
            "python -m pip install -r backend\\requirements.txt"
        ) from error

    output_dir.mkdir(parents=True, exist_ok=True)
    model = YOLO(model_name)
    results = model.train(
        data=str(config_path),
        epochs=epochs,
        imgsz=image_size,
        project=str(output_dir / "runs"),
        name="waste_detector",
        exist_ok=True,
    )

    best_weights = Path(results.save_dir) / "weights" / "best.pt"
    if not best_weights.is_file():
        raise FileNotFoundError(f"YOLO training did not produce best.pt: {best_weights}")

    stable_model = output_dir / "waste_detector.pt"
    stable_model.write_bytes(best_weights.read_bytes())
    print(f"Training complete. Best model saved to: {stable_model}")
    print(f"Training results: {results.save_dir}")
    return stable_model


def parse_args() -> argparse.Namespace:
    """Parse command-line training options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_CONFIG)
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    """Validate configuration and start model training."""
    args = parse_args()
    if args.epochs < 1 or args.imgsz < 32:
        raise ValueError("--epochs must be positive and --imgsz must be at least 32")
    train_model(args.data.resolve(), args.output.resolve(), args.model, args.epochs, args.imgsz)


if __name__ == "__main__":
    main()
