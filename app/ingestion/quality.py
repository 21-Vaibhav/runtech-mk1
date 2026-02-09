from dataclasses import dataclass
import math


@dataclass
class QualityResult:
    score: float
    flags: dict[str, bool]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list[float]) -> float:
    if not values:
        return 0.0
    m = _mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / len(values))


def assess_stream_quality(streams: dict) -> QualityResult:
    """Compute robust run-level quality score in [0,1]."""
    flags = {
        "missing_streams": False,
        "gps_drift": False,
        "hr_flatline": False,
        "hr_out_of_range": False,
        "incomplete": False,
    }

    velocity = streams.get("velocity_smooth", {}).get("data", [])
    heartrate = streams.get("heartrate", {}).get("data", [])
    time_stream = streams.get("time", {}).get("data", [])

    if not velocity or not heartrate or not time_stream:
        flags["missing_streams"] = True

    if velocity:
        high = any(v > 8.5 for v in velocity)
        very_low = sum(1 for v in velocity if v < 0.3) > max(2, int(len(velocity) * 0.3))
        if high or very_low:
            flags["gps_drift"] = True

    if heartrate:
        if _std(heartrate) < 1.5:
            flags["hr_flatline"] = True
        if any(hr < 40 or hr > 220 for hr in heartrate) or _mean(heartrate) < 70:
            flags["hr_out_of_range"] = True

    if time_stream and len(time_stream) < 30:
        flags["incomplete"] = True

    penalties = {
        "missing_streams": 0.35,
        "gps_drift": 0.2,
        "hr_flatline": 0.2,
        "hr_out_of_range": 0.15,
        "incomplete": 0.1,
    }
    score = 1.0 - sum(penalties[name] for name, active in flags.items() if active)
    return QualityResult(score=max(0.0, min(1.0, score)), flags=flags)
