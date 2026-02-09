from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.storage.repository import DailyRecommendation, FeedbackEvent


@dataclass
class FeedbackResult:
    compliance: bool
    calibration_flag: str | None


def register_feedback(db: Session, day: date, actual_action: str) -> FeedbackResult:
    rec = db.scalar(select(DailyRecommendation).where(DailyRecommendation.day == day))
    if not rec:
        raise ValueError("No recommendation found for that day")

    compliance = rec.action == actual_action
    bias = "over_reached" if (actual_action == "hard" and rec.action in {"rest", "easy"}) else None

    event = FeedbackEvent(
        day=day,
        recommended_action=rec.action,
        actual_action=actual_action,
        compliance=compliance,
        expected_outcome={"fitness": rec.expected_fitness_delta, "fatigue": rec.expected_fatigue_delta},
        observed_outcome=None,
        calibration_flag=bias,
    )
    db.add(event)
    db.commit()
    return FeedbackResult(compliance=compliance, calibration_flag=bias)
