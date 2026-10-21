"""EcoVision AI FastAPI application."""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import connection, initialize_database
from .recommendation import get_recommendation
from .schemas import DetectionRequest, DetectionResponse, StatisticsResponse

app = FastAPI(
    title="EcoVision AI",
    description="Real-time smart waste detection and recycling assistant.",
    version="0.1.0",
)
FRONTEND_PATH = Path(__file__).resolve().parents[2] / "frontend"


@app.on_event("startup")
def startup() -> None:
    """Initialize local persistence when the API starts."""
    initialize_database()


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    """Return a welcome message for the API root."""
    return {"message": "Welcome to EcoVision AI"}


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Report whether the API is available."""
    return {"status": "ok"}


@app.get("/model/status", tags=["system"])
def model_status() -> dict[str, object]:
    """Report whether an optional trained model is available."""
    model_path = Path("ml/models/waste_detector.pt")
    return {"mode": "model" if model_path.is_file() else "demo", "model_available": model_path.is_file()}


@app.post("/detect", response_model=DetectionResponse, status_code=201, tags=["detections"])
def create_detection(request: DetectionRequest) -> DetectionResponse:
    """Persist a detection and return its disposal recommendation."""
    recommendation = get_recommendation(request.waste_type, request.confidence)
    timestamp = datetime.now(timezone.utc)
    with connection() as database:
        cursor = database.execute(
            """
            INSERT INTO detections
            (waste_type, confidence, category, recommended_bin, recommendation_message, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (request.waste_type, request.confidence, recommendation.category,
             recommendation.recommended_bin, recommendation.message, timestamp.isoformat()),
        )
        detection_id = cursor.lastrowid
    return DetectionResponse(
        id=detection_id,
        **request.model_dump(),
        category=recommendation.category,
        recommended_bin=recommendation.recommended_bin,
        recommendation_message=recommendation.message,
        timestamp=timestamp,
    )


@app.get("/detections", response_model=list[DetectionResponse], tags=["detections"])
def list_detections(limit: int = Query(default=20, ge=1, le=100)) -> list[DetectionResponse]:
    """Return the most recent detections."""
    with connection() as database:
        rows = database.execute(
            "SELECT * FROM detections ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    return [DetectionResponse(**dict(row)) for row in rows]


@app.get("/statistics", response_model=StatisticsResponse, tags=["statistics"])
def statistics() -> StatisticsResponse:
    """Return counts for the dashboard."""
    today = datetime.now(timezone.utc).date().isoformat()
    with connection() as database:
        total = database.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
        today_count = database.execute(
            "SELECT COUNT(*) FROM detections WHERE substr(timestamp, 1, 10) = ?", (today,)
        ).fetchone()[0]
        rows = database.execute(
            "SELECT waste_type, COUNT(*) AS count FROM detections GROUP BY waste_type"
        ).fetchall()
    return StatisticsResponse(
        total_detections=total,
        today_detections=today_count,
        distribution={row["waste_type"]: row["count"] for row in rows},
    )


@app.get("/recommendation/{waste_type}", tags=["recommendations"])
def recommendation(waste_type: str, confidence: float = Query(default=0.9, ge=0, le=1)) -> dict[str, str]:
    """Return the centralized recommendation for a waste type."""
    try:
        result = get_recommendation(waste_type, confidence)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return {
        "waste_type": waste_type,
        "category": result.category,
        "recommended_bin": result.recommended_bin,
        "recommendation_message": result.message,
    }


@app.get("/app", include_in_schema=False)
def dashboard() -> FileResponse:
    """Serve the local dashboard."""
    return FileResponse(FRONTEND_PATH / "index.html")


if FRONTEND_PATH.is_dir():
    app.mount("/static", StaticFiles(directory=FRONTEND_PATH), name="static")
