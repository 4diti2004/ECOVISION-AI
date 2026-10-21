"""Standalone webcam detector for a trained EcoVision YOLO model."""

from __future__ import annotations

import argparse
from pathlib import Path

from backend.app.recommendation import RECOMMENDATIONS


def run(model_path: Path, camera_index: int, confidence: float) -> None:
    """Open a webcam, run YOLO inference, and close it safely."""
    try:
        import cv2
        from ultralytics import YOLO
    except ImportError as error:
        raise RuntimeError(
            "Install the ML dependencies first with "
            "python -m pip install -r backend\\requirements.txt"
        ) from error

    if not model_path.is_file():
        raise FileNotFoundError(
            f"Model not found: {model_path}. Train a model or set --model to a .pt file."
        )

    model = YOLO(str(model_path))
    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        raise RuntimeError(f"Could not open webcam index {camera_index}. Check camera permissions.")

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError("The webcam returned an invalid frame.")

            results = model(frame, conf=confidence, verbose=False)
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    score = float(box.conf[0])
                    waste_type = str(result.names[class_id]).lower().replace(" ", "_")
                    label = f"{waste_type} {score:.0%}"
                    left, top, right, bottom = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (left, top), (right, bottom), (50, 210, 130), 2)
                    cv2.putText(
                        frame, label, (left, max(20, top - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (50, 210, 130), 2,
                    )
                    if waste_type in RECOMMENDATIONS:
                        cv2.putText(
                            frame, RECOMMENDATIONS[waste_type].recommended_bin,
                            (left, min(frame.shape[0] - 10, bottom + 22)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
                        )

            cv2.imshow("EcoVision AI - press Q to quit", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()


def main() -> None:
    """Parse CLI options and start webcam inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=Path("ml/models/waste_detector.pt"))
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--confidence", type=float, default=0.5)
    args = parser.parse_args()
    if not 0 <= args.confidence <= 1:
        raise ValueError("--confidence must be between 0 and 1")
    run(args.model, args.camera, args.confidence)


if __name__ == "__main__":
    main()
