from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.quality import assess_stream_quality
from app.ingestion.strava_client import StravaClient
from app.storage.repository import Activity, ActivityStream


STREAM_NAME_MAP = {
    "time": "time",
    "velocity_smooth": "velocity_smooth",
    "heartrate": "heartrate",
    "altitude": "altitude",
}


def sync_strava_activities(db: Session, client: StravaClient, after: datetime | None = None) -> dict:
    fetched = updated = skipped = 0
    for item in client.iter_activities(after=after):
        fetched += 1
        existing = db.scalar(select(Activity).where(Activity.strava_id == item["id"]))
        if existing:
            skipped += 1
            continue

        streams = client.get_streams(item["id"])
        quality = assess_stream_quality(streams)
        activity = Activity(
            strava_id=item["id"],
            started_at=datetime.fromisoformat(item["start_date"].replace("Z", "+00:00")),
            distance_m=item.get("distance", 0.0),
            moving_time_s=item.get("moving_time", 0),
            elapsed_time_s=item.get("elapsed_time", 0),
            avg_hr=item.get("average_heartrate"),
            max_hr=item.get("max_heartrate"),
            data_quality_score=quality.score,
            anomaly_flags=quality.flags,
        )
        db.add(activity)
        db.flush()
        for key, stream_name in STREAM_NAME_MAP.items():
            data = streams.get(key, {}).get("data")
            if data is None:
                continue
            db.add(ActivityStream(activity_id=activity.id, stream_type=stream_name, values=data))
        updated += 1
    db.commit()
    return {"fetched_activities": fetched, "updated_activities": updated, "skipped_activities": skipped}
