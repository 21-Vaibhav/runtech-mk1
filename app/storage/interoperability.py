import csv
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.storage.repository import Activity, DailyRecommendation, FeedbackEvent


@dataclass
class ManualWorkout:
    started_at: datetime
    distance_m: float
    moving_time_s: int
    avg_hr: float | None = None


def add_manual_workout(db: Session, workout: ManualWorkout) -> Activity:
    synthetic_id = int(workout.started_at.timestamp())
    activity = Activity(
        strava_id=synthetic_id,
        started_at=workout.started_at,
        distance_m=workout.distance_m,
        moving_time_s=workout.moving_time_s,
        elapsed_time_s=workout.moving_time_s,
        avg_hr=workout.avg_hr,
        max_hr=workout.avg_hr,
        data_quality_score=0.8,
        anomaly_flags={"manual_entry": True},
    )
    db.merge(activity)
    db.commit()
    return activity


def export_csv_bundle(db: Session, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []

    recs_file = output_dir / "decisions.csv"
    with recs_file.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["day", "action", "fitness_delta", "fatigue_delta", "confidence"])
        writer.writeheader()
        for r in db.scalars(select(DailyRecommendation).order_by(DailyRecommendation.day.asc())).all():
            writer.writerow(
                {
                    "day": r.day.isoformat(),
                    "action": r.action,
                    "fitness_delta": r.expected_fitness_delta,
                    "fatigue_delta": r.expected_fatigue_delta,
                    "confidence": r.decision_confidence,
                }
            )
    files.append(recs_file)

    fb_file = output_dir / "feedback.csv"
    with fb_file.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["day", "recommended", "actual", "compliance", "calibration_flag"])
        writer.writeheader()
        for e in db.scalars(select(FeedbackEvent).order_by(FeedbackEvent.day.asc())).all():
            writer.writerow(
                {
                    "day": e.day.isoformat(),
                    "recommended": e.recommended_action,
                    "actual": e.actual_action,
                    "compliance": e.compliance,
                    "calibration_flag": e.calibration_flag,
                }
            )
    files.append(fb_file)
    return files
