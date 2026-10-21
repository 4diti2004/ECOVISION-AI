"""Centralized waste classification and recommendation rules."""

from dataclasses import dataclass

CONFIDENCE_THRESHOLD = 0.5


@dataclass(frozen=True)
class Recommendation:
    """Recommendation details for a waste type."""

    category: str
    recommended_bin: str
    message: str


RECOMMENDATIONS = {
    "plastic": Recommendation("Recyclable", "Dry/Recyclable Waste", "Rinse and place in dry recyclable waste."),
    "paper": Recommendation("Recyclable", "Paper Recycling", "Keep paper clean and dry for recycling."),
    "cardboard": Recommendation("Recyclable", "Paper/Cardboard Recycling", "Flatten cardboard and keep it dry."),
    "glass": Recommendation("Recyclable", "Glass Recycling", "Handle carefully and place in glass recycling."),
    "metal": Recommendation("Recyclable", "Metal Recycling", "Empty and place in metal recycling."),
    "organic": Recommendation("Compostable", "Organic Waste", "Place food and garden waste in composting."),
    "e_waste": Recommendation("Special Handling", "E-Waste Collection", "Take electronics to an authorized e-waste collection point."),
    "other": Recommendation("General Waste", "General Waste", "Place in general waste when no specialist stream applies."),
}


def get_recommendation(waste_type: str, confidence: float) -> Recommendation:
    """Return a safe recommendation, warning when confidence is low."""
    recommendation = RECOMMENDATIONS.get(waste_type)
    if recommendation is None:
        raise ValueError(f"Unsupported waste type: {waste_type}")
    if confidence < CONFIDENCE_THRESHOLD:
        return Recommendation(
            recommendation.category,
            recommendation.recommended_bin,
            f"Low-confidence detection ({confidence:.0%}). Verify the item before disposal.",
        )
    return recommendation
