"""Assignment 2 category-based, two-model cascade.

The classification prompt and parser are imported unchanged from Assignment 1.
The small model always runs first; a larger model supplies the final category
when the predicted small-model category is not in the accepted set.
"""
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from app.config import settings
from app.services.classifier import classify_ticket

ACCEPTED_CATEGORIES = {
    "A": frozenset({"Mortgage"}),
    "B": frozenset({"Mortgage", "Bank account or service"}),
}


@dataclass(frozen=True)
class CascadeResult:
    category: str
    first_category: str
    final_model: str
    escalated: bool
    first_stage_ms: float
    second_stage_ms: float


def classify_with_cascade(narrative: str, request: Any | None = None) -> CascadeResult:
    setting = settings.cascade_setting
    if setting not in ACCEPTED_CATEGORIES:
        raise ValueError("CASCADE_SETTING must be A or B")
    small = settings.cascade_small_model
    large = settings.cascade_large_model
    if not small or not large or small == large:
        raise ValueError("The two cascade model tags must be distinct and non-empty")

    # Metadata is also made available for failed requests, with no complaint text.
    if request is not None:
        request.state.first_model = small
        request.state.final_model = None
        request.state.escalated = None
        request.state.escalation_setting = setting

    first_start = perf_counter()
    first_category = classify_ticket(narrative, model=small)
    first_ms = (perf_counter() - first_start) * 1000
    if request is not None:
        request.state.first_stage_ms = round(first_ms, 3)
        request.state.first_category = first_category

    escalated = first_category not in ACCEPTED_CATEGORIES[setting]
    if request is not None:
        request.state.escalated = escalated
        request.state.final_model = large if escalated else small

    second_ms = 0.0
    final_category = first_category
    if escalated:
        second_start = perf_counter()
        final_category = classify_ticket(narrative, model=large)
        second_ms = (perf_counter() - second_start) * 1000
        if request is not None:
            request.state.second_stage_ms = round(second_ms, 3)

    return CascadeResult(
        category=final_category,
        first_category=first_category,
        final_model=large if escalated else small,
        escalated=escalated,
        first_stage_ms=first_ms,
        second_stage_ms=second_ms,
    )
