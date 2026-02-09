from dataclasses import dataclass


@dataclass
class StructuredSummary:
    fitness: float
    fitness_ci: tuple[float, float]
    fatigue: float
    fatigue_ci: tuple[float, float]
    form: float
    efficiency_change_pct: float
    load_spike: bool
    decision: str
    confidence: str


class LocalNarrativeLLM:
    """Narrative-only adapter. Never computes analysis from raw activity data."""

    def __init__(self, model_name: str = "phi-3-mini"):
        self.model_name = model_name

    def explain(self, summary: StructuredSummary, question: str) -> str:
        spike_msg = "A recent load spike increased caution." if summary.load_spike else "Load is currently stable."
        return (
            f"Decision: {summary.decision}. "
            f"Form is {summary.form:.1f} with confidence {summary.confidence}. "
            f"Efficiency changed by {summary.efficiency_change_pct:.1f}%. "
            f"{spike_msg} "
            f"Question received: '{question}'. "
            "This narrative is generated from structured metrics only."
        )
