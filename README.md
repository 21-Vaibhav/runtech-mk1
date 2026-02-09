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

Open `http://127.0.0.1:8000/` for the minimal UI.

## Minimal UI workflow

1. Paste your Strava access token and click **Sync**.
2. Click **Refresh State**.
3. Choose training phase and click **Get Recommendation**.
4. Ask **Explain** questions (narrative only).

## How to connect Strava API

1. Create an app at `https://www.strava.com/settings/api`.
2. Set Authorization Callback Domain to `localhost`.
3. Get `client_id` and `client_secret`.
4. Authorize once in browser:
   ```
   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all
   ```
5. Exchange code for token:
   ```bash
   curl -X POST https://www.strava.com/oauth/token \
     -d client_id=YOUR_CLIENT_ID \
     -d client_secret=YOUR_CLIENT_SECRET \
     -d code=CODE_FROM_STEP_4 \
     -d grant_type=authorization_code
   ```
6. Copy `access_token` into the UI Sync box.

> Tip: Strava tokens expire; use `refresh_token` with the same `/oauth/token` endpoint and `grant_type=refresh_token`.

## How to install and connect a local LLM

### Option A (recommended): Ollama (fully local)

1. Install Ollama: `https://ollama.com/download`
2. Pull a model (example):
   ```bash
   ollama pull phi3:mini
   ```
3. Start app with Ollama mode:
   ```bash
   export LLM_MODE=ollama
   export OLLAMA_MODEL=phi3:mini
   export OLLAMA_BASE_URL=http://127.0.0.1:11434
   uvicorn app.main:app --reload
   ```

If Ollama is unavailable, the project falls back to deterministic local narrative text.

### Option B: online API key (possible, but not recommended)

You *can* wire an online/free API key provider, but that breaks strict local-first privacy and your original constraints.
For serious privacy-focused usage, keep LLM mode local (`LLM_MODE=ollama` or default local stub).

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
- CSV export and manual workout entry hooks are in `app/storage`.
