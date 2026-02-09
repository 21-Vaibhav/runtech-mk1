from dataclasses import dataclass

import httpx

from app.config import settings


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

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.ollama_model

    def _build_prompt(self, summary: StructuredSummary, question: str) -> str:
        return (
            "You are a running coach assistant. Use only provided structured metrics. "
            "Do not invent calculations. Keep uncertainty explicit.\n"
            f"summary={summary}\n"
            f"question={question}\n"
        )

    def _fallback(self, summary: StructuredSummary, question: str) -> str:
        spike_msg = "A recent load spike increased caution." if summary.load_spike else "Load is currently stable."
        return (
            f"Decision: {summary.decision}. "
            f"Form is {summary.form:.1f} with confidence {summary.confidence}. "
            f"Efficiency changed by {summary.efficiency_change_pct:.1f}%. "
            f"{spike_msg} "
            f"Question received: '{question}'. "
            "This narrative is generated from structured metrics only."
        )

    def _explain_with_ollama(self, summary: StructuredSummary, question: str) -> str:
        prompt = self._build_prompt(summary, question)
        response = httpx.post(
            f"{settings.ollama_base_url}/api/generate",
            json={"model": self.model_name, "prompt": prompt, "stream": False},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("response", "")

    def explain(self, summary: StructuredSummary, question: str) -> str:
        if settings.llm_mode == "ollama":
            try:
                return self._explain_with_ollama(summary, question)
            except Exception:
                return self._fallback(summary, question)
        return self._fallback(summary, question)
