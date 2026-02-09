import time
from collections.abc import Iterable
from datetime import datetime

import httpx

from app.config import settings


class StravaClient:
    """Small Strava V3 client with conservative rate-limit handling."""

    def __init__(self, access_token: str):
        self._client = httpx.Client(
            base_url=settings.strava_base_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=20,
        )

    def _safe_get(self, url: str, params: dict | None = None) -> httpx.Response:
        response = self._client.get(url, params=params)
        short_limit = response.headers.get("X-RateLimit-Usage")
        if response.status_code == 429:
            time.sleep(settings.strava_rate_limit_buffer_seconds)
            response = self._client.get(url, params=params)
        if short_limit:
            time.sleep(0.15)
        response.raise_for_status()
        return response

    def iter_activities(self, after: datetime | None = None) -> Iterable[dict]:
        page = 1
        while True:
            params = {"page": page, "per_page": settings.strava_page_size}
            if after:
                params["after"] = int(after.timestamp())
            payload = self._safe_get("/athlete/activities", params=params).json()
            if not payload:
                break
            for item in payload:
                yield item
            page += 1

    def get_streams(self, activity_id: int) -> dict:
        keys = "time,velocity_smooth,heartrate,altitude"
        response = self._safe_get(f"/activities/{activity_id}/streams", params={"keys": keys, "key_by_type": True})
        return response.json()
