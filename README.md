# RunTech MK1 (Local-First Running Decision MVP)

A layered running performance system focused on physiology, uncertainty, and daily action selection.

## Architecture

1. **Data ingestion** (`app/ingestion`) from Strava V3 (OAuth token-based calls).
2. **Modeling** (`app/modeling`) using low-parameter online updates for fitness/fatigue/form.
3. **Signal derivation** (`app/signals`) as structured metrics only.
4. **Decision engine** (`app/decision`) constrained action optimization over discrete actions.
5. **Feedback loop** (`app/feedback`) tracking recommendation quality and compliance.
6. **LLM narrative** (`app/llm`) with structured summaries only (no raw data or analysis).

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Endpoints

- `POST /sync?access_token=...`
- `GET /state`
- `GET /recommendation?phase=build`
- `POST /explain`
- `POST /feedback`

## Notes on design constraints

- SQLite-only local storage (`data/runtech.db`).
- Rate-limit safe sync with idempotent de-duplication by Strava activity id.
- Each activity gets a `data_quality_score` and anomaly flags.
- Decision logic is scoring + hard constraints, not simple if/else output tables.
- LLM layer is narrative-only and receives pre-computed structured summaries.
- CSV export and manual workout entry hooks can be added in `app/storage` and a CLI module.
