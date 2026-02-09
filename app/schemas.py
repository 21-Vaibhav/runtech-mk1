from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Action = Literal["rest", "easy", "moderate", "hard"]


class SyncResponse(BaseModel):
    fetched_activities: int
    updated_activities: int
    skipped_activities: int


class ModelStateResponse(BaseModel):
    as_of: date
    fitness: float
    fatigue: float
    form: float
    efficiency: float
    drift_onset_min: float | None
    confidence: float


class RecommendationResponse(BaseModel):
    day: date
    action: Action
    expected_fitness_delta: float
    expected_fatigue_delta: float
    decision_confidence: float = Field(ge=0.0, le=1.0)
    constraints_applied: list[str]


class ExplainRequest(BaseModel):
    question: str


class ExplainResponse(BaseModel):
    answer: str


class FeedbackRequest(BaseModel):
    day: date
    actual_action: Action


class FeedbackResponse(BaseModel):
    compliance: bool
    calibration_flag: str | None
