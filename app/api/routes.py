from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.feedback.tracker import register_feedback
from app.ingestion.sync_service import sync_strava_activities
from app.ingestion.strava_client import StravaClient
from app.llm.narrative import LocalNarrativeLLM, StructuredSummary
from app.modeling.state_model import estimate_state
from app.decision.engine import choose_action
from app.schemas import (
    ExplainRequest,
    ExplainResponse,
    FeedbackRequest,
    FeedbackResponse,
    ModelStateResponse,
    RecommendationResponse,
    SyncResponse,
)
from app.storage.repository import Activity, DailyRecommendation

router = APIRouter()
llm = LocalNarrativeLLM()


@router.post("/sync", response_model=SyncResponse)
def sync(access_token: str, db: Session = Depends(get_db)) -> SyncResponse:
    client = StravaClient(access_token=access_token)
    return SyncResponse(**sync_strava_activities(db, client))


@router.get("/state", response_model=ModelStateResponse)
def state(db: Session = Depends(get_db)) -> ModelStateResponse:
    m = estimate_state(db)
    return ModelStateResponse(
        as_of=date.today(),
        fitness=m.fitness,
        fatigue=m.fatigue,
        form=m.form,
        efficiency=m.efficiency,
        drift_onset_min=m.drift_onset_min,
        confidence=m.confidence,
    )


@router.get("/recommendation", response_model=RecommendationResponse)
def recommendation(phase: str = "build", db: Session = Depends(get_db)) -> RecommendationResponse:
    state_now = estimate_state(db)
    decision = choose_action(db, state_now, phase=phase)
    return RecommendationResponse(
        day=date.today(),
        action=decision.action,
        expected_fitness_delta=decision.expected_fitness_delta,
        expected_fatigue_delta=decision.expected_fatigue_delta,
        decision_confidence=decision.confidence,
        constraints_applied=decision.constraints,
    )


@router.post("/explain", response_model=ExplainResponse)
def explain(payload: ExplainRequest, db: Session = Depends(get_db)) -> ExplainResponse:
    rec = db.scalar(select(DailyRecommendation).order_by(DailyRecommendation.day.desc()))
    state_now = estimate_state(db)
    latest_activity = db.scalar(select(Activity).order_by(Activity.started_at.desc()))
    if not rec:
        raise HTTPException(status_code=404, detail="No recommendation available")

    summary = StructuredSummary(
        fitness=state_now.fitness,
        fitness_ci=(state_now.fitness - 5, state_now.fitness + 5),
        fatigue=state_now.fatigue,
        fatigue_ci=(state_now.fatigue - 5, state_now.fatigue + 5),
        form=state_now.form,
        efficiency_change_pct=0.0,
        load_spike=bool(latest_activity and latest_activity.anomaly_flags.get("gps_drift")),
        decision=rec.action,
        confidence="medium" if rec.decision_confidence > 0.5 else "low",
    )
    return ExplainResponse(answer=llm.explain(summary, payload.question))


@router.post("/feedback", response_model=FeedbackResponse)
def feedback(payload: FeedbackRequest, db: Session = Depends(get_db)) -> FeedbackResponse:
    try:
        outcome = register_feedback(db, day=payload.day, actual_action=payload.actual_action)
        return FeedbackResponse(compliance=outcome.compliance, calibration_flag=outcome.calibration_flag)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
