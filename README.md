# AgriPulse

Evidence-first agricultural decision intelligence for Coimbatore, Erode, and
Salem (Tomato + Onion). Data → BigQuery → deterministic agents → Gemini
explanation → React UI.

This repo is organized by the same phases as the build plan:

```
agripulse/
├── infra/           Phase: BigQuery schema, seed data, deployment scripts
├── ingestion/        Phase: pulls weather/market/crop data into BigQuery
├── agents/            Phase: Weather/Soil/Market agents + Decision Engine + Orchestrator
├── backend/           Phase: FastAPI service exposing it all
├── frontend/          Phase: React UI
├── Dockerfile          Phase: bundles frontend + backend for Cloud Run
└── requirements.txt
```

## Quickstart — run everything locally with mock data (no GCP needed)

The whole stack runs without any cloud credentials using local JSON fixtures
(`agents/fixtures/*.json`) and a local JSON farm store
(`backend/local_farms.json`, created automatically). This is the fastest way
to see the full pipeline working.

```bash
# 1. Backend
pip install -r requirements.txt
cd backend
AGRIPULSE_MOCK_DATA=1 uvicorn main:app --reload --port 8080

# 2. Frontend (separate terminal)
cd frontend
npm install
npm run dev
# open http://localhost:5173
```

Try the pre-seeded mock farm: create a farm with district=Coimbatore,
crop=Tomato in the UI, or query directly:

```bash
curl -X POST localhost:8080/farm -H "Content-Type: application/json" \
  -d '{"district":"Coimbatore","crop":"Tomato","growth_stage":"Flowering"}'
```

Run the test suite (33 agent/decision-engine tests + 5 API tests):

```bash
cd agents && AGRIPULSE_MOCK_DATA=1 python -m pytest tests/ -v && cd ..
cd backend && AGRIPULSE_MOCK_DATA=1 python -m pytest tests/ -v && cd ..
```

Both suites, plus a frontend build check, run automatically on every push via
`.github/workflows/ci.yml`.

You can also run any single agent standalone:

```bash
cd agents
AGRIPULSE_MOCK_DATA=1 python weather_agent.py
AGRIPULSE_MOCK_DATA=1 python orchestrator.py
```

## Setting API keys via .env (instead of manual `export`)

The project supports a `.env` file at the project root — `python-dotenv` is wired
into every entry point (`backend/main.py`, `agents/orchestrator.py`,
`agents/bq_helper.py`, `backend/farm_store.py`, `ingestion/gcp_clients.py`) and
finds `.env` automatically regardless of which subfolder you run commands from.

```bash
cp .env.example .env
# then edit .env and fill in real values, e.g.:
#   GEMINI_API_KEY=AIza...
#   DATA_GOV_IN_API_KEY=579b464...
#   GCP_PROJECT_ID=your-project-id
#   AGRIPULSE_MOCK_DATA=0
```

That's it — no more `export VAR=value` before every command. Just run things
normally:

```bash
cd backend
uvicorn main:app --reload --port 8080   # picks up .env automatically
```

**Notes:**
- `.env` is gitignored by convention — never commit real keys. Add a `.gitignore`
  with a `.env` line if you're pushing this to GitHub (not included by default).
- A value already set in your shell (`export FOO=bar`) takes priority over
  `.env` — `load_dotenv()` won't override an existing environment variable
  unless you pass `override=True`, which this project doesn't. If you're not
  seeing your `.env` change take effect, check you don't have a stale
  `export` from an earlier terminal session shadowing it.
- Restart `uvicorn --reload` after editing `.env` — the file is only read once
  at process start, not on every request.

## Going from mock to real data

### 1. GCP project setup

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable bigquery.googleapis.com storage.googleapis.com \
  firestore.googleapis.com run.googleapis.com cloudscheduler.googleapis.com
gsutil mb -l asia-south1 gs://agripulse-raw
gsutil mb -l asia-south1 gs://agripulse-processed
```

### 2. Create the BigQuery schema

```bash
bq query --use_legacy_sql=false < infra/bigquery_schema.sql
```

### 3. Seed with synthetic farm + soil data (10 Coimbatore farms, 90 days of soil readings)

```bash
bq query --use_legacy_sql=false < infra/synthetic_seed_data.sql
```

### 4. Get API keys

- **Gemini**: create a key at https://aistudio.google.com/apikey → set `GEMINI_API_KEY`
- **data.gov.in** (Agmarknet market prices): register at https://data.gov.in → set `DATA_GOV_IN_API_KEY`

### 5. Run ingestion for real weather + market data

```bash
cd ingestion
export GCP_PROJECT_ID=your-project GEMINI_API_KEY=... DATA_GOV_IN_API_KEY=...
python weather_ingest.py
python market_ingest.py
# crop_history is annual — download the CSV from data.gov.in first, then:
RAW_CSV_PATH=/path/to/download.csv python crop_history_ingest.py
```

### 6. Switch agents/backend off mock mode

```bash
export AGRIPULSE_MOCK_DATA=0
export GCP_PROJECT_ID=your-project
export GEMINI_API_KEY=...
```

## Deployment (Cloud Run)

```bash
cd infra
PROJECT_ID=your-project ./deploy.sh
```

This builds the combined Docker image (frontend bundled into the FastAPI
static route — see `Dockerfile`), deploys to Cloud Run, and attempts to wire
up a daily Cloud Scheduler job for ingestion. Deploy the ingestion job
separately first using `infra/Dockerfile.ingest` if you want the scheduler
step to succeed on first run:

```bash
gcloud builds submit --tag gcr.io/$PROJECT_ID/agripulse-ingest -f infra/Dockerfile.ingest .
gcloud run jobs create agripulse-ingest \
  --image gcr.io/$PROJECT_ID/agripulse-ingest \
  --region asia-south1 \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID,BQ_DATASET=agripulse_data,AGRIPULSE_MOCK_DATA=0 \
  --set-secrets DATA_GOV_IN_API_KEY=data-gov-in-key:latest
```

Store secrets in Secret Manager first:

```bash
echo -n "your-gemini-key" | gcloud secrets create gemini-api-key --data-file=-
echo -n "your-datagovin-key" | gcloud secrets create data-gov-in-key --data-file=-
```

## Dashboard (Looker Studio)

1. Open Looker Studio → Create → Report → BigQuery → select `agripulse_data`.
2. Build charts against the views, not raw tables:
   - `v_rainfall_7day` → rainfall/temp trend
   - `v_weekly_price_trend` → price trend + % change
   - `v_yield_trend` → historical yield by year
   - `v_latest_soil` → current soil snapshot per farm
3. Share the report link and embed it in the frontend, or link out from a
   "View full dashboard" button (not built into the UI yet — trivial to add
   as an `<a>` tag in `App.jsx`).

## Design decisions worth knowing about

- **Decision Engine is rule-based, not LLM-generated** (`agents/decision_engine.py`).
  Gemini only explains recommendations that already exist — this keeps every
  output reproducible and auditable, which matters a lot when someone asks
  "why did it say that."
- **Mock mode everywhere** (`AGRIPULSE_MOCK_DATA=1` by default) — the entire
  stack, including the FastAPI test suite, runs without any GCP credentials.
  This is what let me hand you tested, verified code rather than just
  untested snippets.
- **Agent pattern**: `agents/*.py` are plain Python functions with a defined
  input/output contract, not `google.adk.Agent` subclasses. This runs
  correctly today regardless of `google-adk` package version. If you want
  the literal ADK wrapper, swap each agent module like this:

  ```python
  from google.adk.agents import Agent
  weather_agent = Agent(
      name="weather_agent",
      model="gemini-2.5-flash",
      tools=[get_weather_signal],
      instruction="Analyze rainfall/temp/humidity and flag anything unusual.",
  )
  ```

  and let ADK's `Runner` handle tool-calling instead of `orchestrator.py`'s
  manual routing — the underlying `get_weather_signal` etc. functions don't
  need to change either way.

## What's not wired up yet (known gaps, on purpose)

- `soil_conditions` real ingestion — intentionally left synthetic per your
  program rules; `infra/synthetic_seed_data.sql` is the source.
- Looker Studio report itself isn't created by code — it's a manual
  point-and-click step against the views above.
- CI (`.github/workflows/ci.yml`) runs tests and builds the frontend, but
  doesn't deploy — deployment stays a manual `infra/deploy.sh` run so you
  control when a demo environment actually changes.
