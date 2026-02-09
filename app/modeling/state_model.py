from dataclasses import dataclass
from datetime import date, datetime
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modeling.load_metrics import rolling_load
from app.storage.repository import Activity, ModelStateSnapshot


@dataclass
class ModelState:
    fitness: float
    fatigue: float
    form: float
    efficiency: float
    drift_onset_min: float | None
    confidence: float


def _ewma(previous: float, x: float, tau_days: float) -> float:
    alpha = 1.0 - math.exp(-1 / tau_days)
    return alpha * x + (1 - alpha) * previous


def estimate_state(db: Session, as_of: datetime | None = None) -> ModelState:
    as_of = as_of or datetime.utcnow()
    latest = db.scalar(select(ModelStateSnapshot).order_by(ModelStateSnapshot.snapshot_date.desc()))
    prev_fit = latest.fitness if latest else 30.0
    prev_fat = latest.fatigue if latest else 25.0
    prev_eff = latest.efficiency if latest else 1.0

    acute = rolling_load(db, as_of, 7)
    chronic = max(1e-6, rolling_load(db, as_of, 28))
    acwr = acute / chronic

    fitness = _ewma(prev_fit, chronic, tau_days=42)
    fatigue = _ewma(prev_fat, acute, tau_days=7)
    form = fitness - fatigue

    latest_activity = db.scalar(select(Activity).order_by(Activity.started_at.desc()))
    quality = latest_activity.data_quality_score if latest_activity else 0.5
    efficiency = _ewma(prev_eff, 1.0 / max(acwr, 0.5), tau_days=21)
    drift_onset = 35.0 if acwr < 1.1 else 25.0
    confidence = max(0.1, min(0.99, quality * (1.0 - abs(acwr - 1.0) * 0.25)))

    snapshot = ModelStateSnapshot(
        snapshot_date=date.fromisoformat(as_of.date().isoformat()),
        fitness=fitness,
        fatigue=fatigue,
        form=form,
        efficiency=efficiency,
        drift_onset_min=drift_onset,
        ci_low=fitness - (1 - confidence) * 8,
        ci_high=fitness + (1 - confidence) * 8,
        confidence=confidence,
    )
    db.merge(snapshot)
    db.commit()
    return ModelState(fitness, fatigue, form, efficiency, drift_onset, confidence)
