from dataclasses import dataclass

from app.modeling.state_model import ModelState


@dataclass
class DerivedSignals:
    fitness_trend: tuple[float, float]
    fatigue_trend: tuple[float, float]
    form: float
    efficiency_delta_pct: float
    drift_onset_change: float | None
    load_spike: bool
    anomaly_flags: list[str]
    confidence: float


def derive_signals(current: ModelState, previous: ModelState | None, data_quality_flags: dict[str, bool]) -> DerivedSignals:
    prev_fit = previous.fitness if previous else current.fitness
    prev_fat = previous.fatigue if previous else current.fatigue
    prev_eff = previous.efficiency if previous else current.efficiency
    prev_drift = previous.drift_onset_min if previous else current.drift_onset_min

    eff_delta = ((current.efficiency - prev_eff) / max(prev_eff, 1e-6)) * 100
    anomaly_flags = [k for k, v in data_quality_flags.items() if v]

    return DerivedSignals(
        fitness_trend=(current.fitness, current.confidence),
        fatigue_trend=(current.fatigue, current.confidence),
        form=current.form,
        efficiency_delta_pct=eff_delta,
        drift_onset_change=(None if current.drift_onset_min is None or prev_drift is None else current.drift_onset_min - prev_drift),
        load_spike=current.fatigue > current.fitness * 1.15,
        anomaly_flags=anomaly_flags,
        confidence=current.confidence,
    )
