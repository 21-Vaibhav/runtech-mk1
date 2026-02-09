from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.storage.repository import Activity


def trimp(activity: Activity, resting_hr: int = 55, max_hr: int = 190) -> float:
    if not activity.avg_hr:
        return 0.0
    intensity = max(0.0, min(1.0, (activity.avg_hr - resting_hr) / (max_hr - resting_hr)))
    duration_min = activity.moving_time_s / 60
    return duration_min * intensity * 1.92


def rolling_load(db: Session, end_dt: datetime, days: int) -> float:
    start_dt = end_dt - timedelta(days=days)
    activities = db.scalars(select(Activity).where(Activity.started_at >= start_dt, Activity.started_at <= end_dt)).all()
    return sum(trimp(a) for a in activities)
