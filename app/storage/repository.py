from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strava_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    distance_m: Mapped[float] = mapped_column(Float)
    moving_time_s: Mapped[int] = mapped_column(Integer)
    elapsed_time_s: Mapped[int] = mapped_column(Integer)
    avg_hr: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_hr: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    anomaly_flags: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    streams: Mapped[list["ActivityStream"]] = relationship(back_populates="activity", cascade="all, delete-orphan")


class ActivityStream(Base):
    __tablename__ = "activity_streams"
    __table_args__ = (UniqueConstraint("activity_id", "stream_type", name="uq_stream_per_activity"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), index=True)
    stream_type: Mapped[str] = mapped_column(String(32), index=True)
    values: Mapped[list[float]] = mapped_column(JSON)

    activity: Mapped[Activity] = relationship(back_populates="streams")


class ModelStateSnapshot(Base):
    __tablename__ = "model_state_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    fitness: Mapped[float] = mapped_column(Float)
    fatigue: Mapped[float] = mapped_column(Float)
    form: Mapped[float] = mapped_column(Float)
    efficiency: Mapped[float] = mapped_column(Float)
    drift_onset_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    ci_low: Mapped[float] = mapped_column(Float)
    ci_high: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)


class DailyRecommendation(Base):
    __tablename__ = "daily_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[date] = mapped_column(Date, unique=True, index=True)
    action: Mapped[str] = mapped_column(String(16))
    rationale_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    expected_fitness_delta: Mapped[float] = mapped_column(Float)
    expected_fatigue_delta: Mapped[float] = mapped_column(Float)
    decision_confidence: Mapped[float] = mapped_column(Float)


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    recommended_action: Mapped[str] = mapped_column(String(16))
    actual_action: Mapped[str | None] = mapped_column(String(16), nullable=True)
    compliance: Mapped[bool] = mapped_column(Boolean, default=False)
    expected_outcome: Mapped[dict[str, Any]] = mapped_column(JSON)
    observed_outcome: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    calibration_flag: Mapped[str | None] = mapped_column(String(64), nullable=True)
