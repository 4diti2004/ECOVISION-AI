"""Pydantic schemas for the EcoVision API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

WasteType = Literal["plastic", "paper", "cardboard", "glass", "metal", "organic", "e_waste", "other"]


class DetectionRequest(BaseModel):
    """A detection submitted by the demo or an ML detector."""

    waste_type: WasteType = "plastic"
    confidence: float = Field(default=0.92, ge=0, le=1)


class DetectionResponse(DetectionRequest):
    """A persisted detection with its recommendation."""

    id: int
    category: str
    recommended_bin: str
    recommendation_message: str
    timestamp: datetime


class StatisticsResponse(BaseModel):
    """Dashboard summary statistics."""

    total_detections: int
    today_detections: int
    distribution: dict[str, int]
