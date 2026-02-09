from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.modeling.load_metrics import rolling_load
from app.modeling.state_model import ModelState
from app.storage.repository import DailyRecommendation

ACTIONS = ["rest", "easy", "moderate", "hard"]
ACTION_EFFECT = {
    "rest": {"fitness": -0.2, "fatigue": -2.5},
    "easy": {"fitness": 0.3, "fatigue": -0.8},
    "moderate": {"fitness": 0.7, "fatigue": 1.0},
    "hard": {"fitness": 1.1, "fatigue": 2.3},
}


@dataclass
class DecisionResult:
    action: str
    expected_fitness_delta: float
    expected_fatigue_delta: float
    confidence: float
    constraints: list[str]


def _phase_multiplier(phase: str, action: str) -> float:
    if phase == "taper" and action in {"moderate", "hard"}:
        return 0.6
    if phase == "peak" and action == "hard":
        return 1.2
    return 1.0


def choose_action(db: Session, state: ModelState, phase: str = "build") -> DecisionResult:
    acute = rolling_load(db, datetime.utcnow(), 7)
    chronic = max(1e-6, rolling_load(db, datetime.utcnow(), 28))
    acwr = acute / chronic

    yesterday = date.today() - timedelta(days=1)
    last = db.scalar(select(DailyRecommendation).where(DailyRecommendation.day == yesterday))
    blocked = set()
    constraints = []

    if state.fatigue - (1 - state.confidence) * 5 > state.fitness:
        blocked.update({"hard"})
        constraints.append("fatigue_ci_danger")
    if last and last.action in {"hard", "moderate"}:
        blocked.update({"hard", "moderate"})
        constraints.append("no_back_to_back_intensity")
    if acwr > settings.acwr_hard_max:
        blocked.update({"hard", "moderate"})
        constraints.append("acwr_hard_cap")
    elif acwr > settings.acwr_soft_max:
        blocked.update({"hard"})
        constraints.append("acwr_soft_cap")

    scored = []
    for action in ACTIONS:
        if action in blocked:
            continue
        effect = ACTION_EFFECT[action]
        score = (effect["fitness"] * _phase_multiplier(phase, action)) - (effect["fatigue"] * 0.45) - abs(acwr - 1.0)
        scored.append((score, action))

    if not scored:
        best = "rest"
    else:
        best = max(scored)[1]

    effect = ACTION_EFFECT[best]
    confidence = max(0.15, min(0.95, state.confidence - len(constraints) * 0.08))
    result = DecisionResult(best, effect["fitness"], effect["fatigue"], confidence, constraints)

    db.merge(
        DailyRecommendation(
            day=date.today(),
            action=result.action,
            rationale_payload={"constraints": result.constraints, "phase": phase, "acwr": acwr},
            expected_fitness_delta=result.expected_fitness_delta,
            expected_fatigue_delta=result.expected_fatigue_delta,
            decision_confidence=result.confidence,
        )
    )
    db.commit()
    return result
