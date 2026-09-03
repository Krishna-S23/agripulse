# AgriPulse: Hardcoded Values & MOCK_DATA Switch Guide

This guide documents all hardcoded values in the AgriPulse codebase and what must be configured when switching from `AGRIPULSE_MOCK_DATA=1` (mock mode) to `AGRIPULSE_MOCK_DATA=0` (production mode with real GCP).

---

## Table of Contents
1. [AGRIPULSE_MOCK_DATA Behavior](#agripulse_mock_data-behavior)
2. [Hardcoded Values by Category](#hardcoded-values-by-category)
3. [Switch from Mock (=1) to Production (=0)](#switch-from-mock-to-production)
4. [Configuration Checklist](#configuration-checklist)

---

## AGRIPULSE_MOCK_DATA Behavior

### When `AGRIPULSE_MOCK_DATA=1` (Default - Mock Mode)
- ✅ **No GCP credentials needed**
- ✅ **Uses local JSON fixtures** for weather, soil, market data
- ✅ **Uses local JSON file** (`backend/local_farms.json`) for farm storage
- ✅ **Faster iteration** - no API calls to external services
- ✅ **Full-stack runnable** - agents, backend, frontend all work

**Files Used:**
- `agents/fixtures/weather.json`
- `agents/fixtures/soil.json`
- `agents/fixtures/market.json`
- `backend/local_farms.json` (created automatically)

### When `AGRIPULSE_MOCK_DATA=0` (Production Mode)
- 📌 **Requires GCP credentials** (via gcloud login or service account)
- 📌 **Reads from BigQuery** for weather, soil, market data
- 📌 **Uses Firestore** for farm profile storage
- 📌 **Makes real API calls** to Vertex AI, data.gov.in, NASA POWER, Open-Meteo
- 📌 **Needs all .env variables set**

---

## Hardcoded Values by Category

### 1. **GCP Resource Names** (from `.env.example`)

| Variable | Hardcoded Default | Used In | Notes |
|----------|-------------------|---------|-------|
| `GCP_PROJECT_ID` | ❌ NONE | All GCP calls | **MUST SET** for production |
| `GCP_REGION` | `us-central1` | Vertex AI | Location for Vertex AI models |
| `BQ_DATASET` | `agripulse_data` | `agents/bq_helper.py`, `ingestion/` | BigQuery dataset name |
| `RAW_BUCKET` | `agripulse-raw` | `ingestion/gcp_clients.py` | GCS bucket for raw data |
| `PROCESSED_BUCKET` | `agripulse-processed` | `ingestion/gcp_clients.py` | GCS bucket for processed data |

**Source:** `ingestion/gcp_clients.py` lines 15-17
```python
DATASET = os.environ.get("BQ_DATASET", "agripulse_data")
RAW_BUCKET = os.environ.get("RAW_BUCKET", "agripulse-raw")
PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET", "agripulse-processed")
```

---

### 2. **BigQuery Table & View Names** (Hardcoded in SQL)

These are **fixed table names** — if you use different names, update the SQL queries.

| Table/View | Location | SQL Query | Notes |
|------------|----------|-----------|-------|
| `agripulse_data.v_rainfall_7day` | `agents/weather_agent.py:11-17` | Used in agents | 7-day weather rolling view |
| `agripulse_data.v_latest_soil` | `agents/soil_agent.py:7-11` | Used in agents | Latest soil reading per farm |
| `agripulse_data.v_weekly_price_trend` | `agents/market_agent.py:7-14` | Used in agents | Weekly aggregated market prices |
| `agripulse_data.farm` | `infra/bigquery_schema.sql:14` | Farm registry | Farm profile master table |
| `agripulse_data.weather` | `infra/bigquery_schema.sql:31` | Raw weather data | Daily weather by district |
| `agripulse_data.soil_conditions` | `infra/bigquery_schema.sql:46` | Raw soil data | Per-farm soil readings |
| `agripulse_data.market_prices` | `infra/bigquery_schema.sql:59` | Raw market data | Daily mandi prices |
| `agripulse_data.crop_history` | `infra/bigquery_schema.sql` | Historical yields | Annual crop production |

**Source:** Each agent file contains the SQL table reference
```python
# weather_agent.py:11-17
SQL = """
  SELECT date, district, rainfall_mm, temperature_c, humidity_pct,
         rain_prob_pct, rainfall_7day_avg
  FROM `agripulse_data.v_rainfall_7day`  # <-- HARDCODED
  WHERE district = @district
  ORDER BY date DESC
  LIMIT 7
"""
```

---

### 3. **Firestore Collection & Schema**

When `AGRIPULSE_MOCK_DATA=0`:

| Item | Value | Location | Notes |
|------|-------|----------|-------|
| Firestore Collection | `farms` | `backend/farm_store.py:51` | Farm profile documents |
| Document ID | `farm_id` | `backend/farm_store.py:51` | Generated as `F{6-hex-chars}` |

**Source:** `backend/farm_store.py` lines 50-51
```python
db = _get_firestore()
db.collection("farms").document(farm_id).set(farm_data)
```

**Expected Schema** (from `backend/models.py`):
```python
{
  "farm_id": "F001ABC",           # auto-generated
  "district": "Coimbatore",       # required
  "crop": "Tomato",               # required: "Tomato" | "Onion"
  "growth_stage": "Flowering",    # optional
  "soil_type": "Loamy",           # optional
  "area_acres": 2.5,              # optional
  "owner_name": "Farmer Name",    # optional
  "location": "Coimbatore, TN",   # optional
}
```

---

### 4. **Decision Engine Thresholds** (Tunable Hardcoded Constants)

These are agricultural rules embedded in Python. **Adjust based on your crop requirements.**

#### Soil Thresholds (`agents/soil_agent.py` lines 14-17)
```python
MOISTURE_LOW = 35          # Percent — below this = LOW_MOISTURE flag
MOISTURE_ADEQUATE = 55     # Percent — at/above this = ADEQUATE_MOISTURE flag
PH_LOW = 6.0               # Below this = PH_OUT_OF_RANGE flag
PH_HIGH = 7.5              # Above this = PH_OUT_OF_RANGE flag
```

#### Weather Thresholds (`agents/weather_agent.py` lines 33-35)
```python
rain_expected = (latest.get("rain_prob_pct") or 0) >= 60    # >= 60% = RAIN_EXPECTED
high_humidity = (latest.get("humidity_pct") or 0) >= 80     # >= 80% = HIGH_HUMIDITY
rainfall_above_avg = ... > ... * 1.3                        # > 130% of avg = RAINFALL_SPIKE
```

#### Market Thresholds (`agents/market_agent.py` lines 16-17)
```python
PRICE_SPIKE_PCT = 8        # >= 8% change = PRICE_ABOVE_TREND
PRICE_DROP_PCT = -8        # <= -8% change = PRICE_BELOW_TREND
```

---

### 5. **Supported Crops & Districts**

These are **conventions in the fixture data and documentation** — not enforced in code, but expected by the UI and ingestion pipeline.

**Supported Districts:**
- `Coimbatore`
- `Erode`
- `Salem`

*Source: Appears in `README.md` and all fixture files*

**Supported Crops:**
- `Tomato`
- `Onion`

*Source: Hardcoded in ingestion pipeline comments and fixtures*

**Fixture Data** (`agents/fixtures/`):
- `weather.json`: Districts = Coimbatore, Erode, Salem
- `soil.json`: Farm IDs = F001, F002, F006, F008
- `market.json`: Crops = Tomato, Onion; Districts = Coimbatore, Erode, Salem

If you want to add new districts/crops:
1. Update ingestion filters (e.g., `ingestion/weather_ingest.py`)
2. Update BigQuery seed data (`infra/synthetic_seed_data.sql`)
3. Update fixture files for mock mode

---

### 6. **External API Endpoints & Keys**

| Service | Endpoint | Auth | Env Variable | Used In |
|---------|----------|------|--------------|---------|
| **NASA POWER** | `https://power.larc.nasa.gov/api/temporal/daily/point` | None | N/A | `ingestion/weather_ingest.py` |
| **Open-Meteo** | `https://api.open-meteo.com/v1/forecast` | None | N/A | `ingestion/weather_ingest.py` |
| **data.gov.in (Agmarknet)** | `https://api.data.gov.in/resource/{RESOURCE_ID}` | API Key | `DATA_GOV_IN_API_KEY` | `ingestion/market_ingest.py` |
| **Vertex AI** | GCP Region-specific | ADC | `GCP_PROJECT_ID`, `GCP_REGION` | `agents/orchestrator.py` |

**Agmarknet Resource ID** (Hardcoded):
```python
# ingestion/market_ingest.py
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
ENDPOINT = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
```

---

### 7. **Vertex AI Model Selection**

Hardcoded default in `.env.example`:
```
VERTEX_AI_MODEL=gemini-2.0-flash
```

**Alternative Models:**
- `gemini-1.5-pro` — more capable, higher cost, slower
- `gemini-1.5-flash` — balanced
- `gemini-2.0-flash` — fastest, latest (recommended)

*Source: `agents/orchestrator.py` line 34*

---

### 8. **Cloud Run Deployment Hardcodes** (from `infra/deploy.sh`)

| Item | Hardcoded Value | Line | Notes |
|------|-----------------|------|-------|
| Service Name | `agripulse-backend` | 8 | Cloud Run service name |
| Region | `asia-south1` | 7 | Can override with `$REGION` env var |
| Mock Data | `0` | 32 | **Sets production mode on deploy** |
| Dataset Name | `agripulse_data` | 32 | Must match BigQuery dataset |
| Scheduler Job | `agripulse-daily-ingest` | 42 | Cloud Scheduler job name |
| Scheduler Schedule | `0 5 * * *` | 45 | 5 AM UTC daily |
| Ingest Job | `agripulse-ingest` | 46 | Cloud Run Job name for ingestion |

**Example from deploy.sh:**
```bash
gcloud run deploy "$SERVICE_NAME" \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},BQ_DATASET=agripulse_data,AGRIPULSE_MOCK_DATA=0" \
  --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,DATA_GOV_IN_API_KEY=data-gov-in-key:latest"
```

---

### 9. **Local Farm Store File** (Mock Mode Only)

When `AGRIPULSE_MOCK_DATA=1`:
- **File:** `backend/local_farms.json` (created automatically)
- **Location:** `backend/farm_store.py` line 16

```python
LOCAL_STORE_PATH = Path(__file__).parent / "local_farms.json"
```

This is a **local JSON file that stores farms in mock mode**. It's `.gitignore`d by default (add if missing).

---

## Switch from Mock to Production

### Step-by-Step: AGRIPULSE_MOCK_DATA=1 → AGRIPULSE_MOCK_DATA=0

#### **Phase 1: Setup GCP Infrastructure** ✅

1. **Create GCP Project**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   export GCP_PROJECT_ID=YOUR_PROJECT_ID
   ```

2. **Enable Required APIs**
   ```bash
   gcloud services enable \
     bigquery.googleapis.com \
     storage.googleapis.com \
     firestore.googleapis.com \
     aiplatform.googleapis.com \
     cloudscheduler.googleapis.com \
     cloudbuild.googleapis.com \
     run.googleapis.com
   ```

3. **Create Cloud Storage Buckets**
   ```bash
   gsutil mb -l asia-south1 gs://agripulse-raw
   gsutil mb -l asia-south1 gs://agripulse-processed
   ```

4. **Create BigQuery Dataset & Tables**
   ```bash
   bq query --project_id="$GCP_PROJECT_ID" --use_legacy_sql=false < infra/bigquery_schema.sql
   ```

5. **Seed Initial Data** (optional but recommended)
   ```bash
   bq query --project_id="$GCP_PROJECT_ID" --use_legacy_sql=false < infra/synthetic_seed_data.sql
   ```

6. **Create Firestore Database** (if not auto-created)
   ```bash
   gcloud firestore databases create --region=asia-south1
   ```

---

#### **Phase 2: Configure Environment** 📝

Create/update `.env` file:
```bash
cp .env.example .env
```

Then edit `.env` with:
```env
# --- GCP Configuration (REQUIRED FOR PRODUCTION) ---
GCP_PROJECT_ID=your-actual-project-id
GCP_REGION=us-central1
BQ_DATASET=agripulse_data
RAW_BUCKET=agripulse-raw
PROCESSED_BUCKET=agripulse-processed

# --- Switch to Production ---
AGRIPULSE_MOCK_DATA=0    # ← CRITICAL: Change from 1 to 0

# --- Vertex AI ---
VERTEX_AI_MODEL=gemini-2.0-flash

# --- External APIs ---
DATA_GOV_IN_API_KEY=your-api-key

# --- Frontend ---
CORS_ORIGINS=*
```

---

#### **Phase 3: Setup Authentication** 🔐

**Option A: Local Development (gcloud)**
```bash
gcloud auth application-default login
```
This sets up ADC (Application Default Credentials) automatically.

**Option B: Service Account (for Cloud Run)**
```bash
# Create service account
gcloud iam service-accounts create agripulse-runner \
  --project=$GCP_PROJECT_ID

# Grant permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:agripulse-runner@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:agripulse-runner@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/firestore.user"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:agripulse-runner@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:agripulse-runner@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

---

#### **Phase 4: Ingest Real Data** 📊

```bash
cd ingestion

# Weather (historical + forecast)
export GCP_PROJECT_ID=your-project-id
python weather_ingest.py

# Market prices (requires DATA_GOV_IN_API_KEY)
export DATA_GOV_IN_API_KEY=your-api-key
python market_ingest.py

# Crop history (manual CSV download from data.gov.in first)
export RAW_CSV_PATH=/path/to/downloaded-crop-data.csv
python crop_history_ingest.py
```

Check BigQuery to verify data loaded:
```bash
bq query "SELECT COUNT(*) as cnt FROM agripulse_data.weather"
bq query "SELECT COUNT(*) as cnt FROM agripulse_data.market_prices"
bq query "SELECT COUNT(*) as cnt FROM agripulse_data.crop_history"
```

---

#### **Phase 5: Test in Production Mode** 🧪

1. **Restart backend with new config**
   ```bash
   cd backend
   # Kill the old uvicorn process, or:
   pkill -f "uvicorn main:app"
   
   # Restart with .env loaded
   uvicorn main:app --reload --port 8080
   ```

2. **Test an API call**
   ```bash
   curl -X POST http://localhost:8080/farm \
     -H "Content-Type: application/json" \
     -d '{
       "district": "Coimbatore",
       "crop": "Tomato",
       "growth_stage": "Flowering"
     }'
   ```

3. **Check if farm was created in Firestore**
   ```bash
   gcloud firestore documents list --collection-id=farms
   ```

4. **Test intelligence endpoint** (data should come from BigQuery now)
   ```bash
   curl http://localhost:8080/intelligence/{farm_id}
   ```

---

#### **Phase 6: Deploy to Cloud Run** 🚀

```bash
cd infra
PROJECT_ID=$GCP_PROJECT_ID ./deploy.sh
```

This will:
- ✅ Enable required APIs
- ✅ Create BigQuery dataset (already done, skipped)
- ✅ Build Docker image
- ✅ Deploy to Cloud Run with `AGRIPULSE_MOCK_DATA=0`
- ✅ Setup Cloud Scheduler for daily ingestion

---

## Configuration Checklist

### **Mock Mode (AGRIPULSE_MOCK_DATA=1)** ✅ Default
- [ ] No `.env` needed (all defaults work)
- [ ] No GCP project required
- [ ] No external API keys needed
- [ ] Fixture files exist (`agents/fixtures/*.json`)
- [ ] `backend/local_farms.json` created automatically

### **Production Mode (AGRIPULSE_MOCK_DATA=0)** 📋

#### **Environment Variables**
- [ ] `GCP_PROJECT_ID` set to your GCP project ID
- [ ] `GCP_REGION` set (default `us-central1`)
- [ ] `BQ_DATASET` set to `agripulse_data` (or custom)
- [ ] `RAW_BUCKET` set to `agripulse-raw` (or custom)
- [ ] `PROCESSED_BUCKET` set to `agripulse-processed` (or custom)
- [ ] `DATA_GOV_IN_API_KEY` set (if using market data)
- [ ] `AGRIPULSE_MOCK_DATA=0`

#### **GCP Resources**
- [ ] GCP project created
- [ ] BigQuery dataset `agripulse_data` created
- [ ] BigQuery tables created (via `bigquery_schema.sql`)
- [ ] BigQuery views created (`v_rainfall_7day`, `v_latest_soil`, `v_weekly_price_trend`)
- [ ] Cloud Storage buckets created (`agripulse-raw`, `agripulse-processed`)
- [ ] Firestore database created
- [ ] Service account with appropriate IAM roles
- [ ] APIs enabled (BigQuery, Storage, Firestore, Vertex AI, Cloud Scheduler)

#### **Data**
- [ ] Weather data ingested (via `weather_ingest.py`)
- [ ] Market data ingested (via `market_ingest.py`)
- [ ] Crop history ingested (via `crop_history_ingest.py`)
- [ ] At least one farm created in Firestore

#### **Authentication**
- [ ] `gcloud auth application-default login` run (local dev)
- [ ] OR service account JSON at `GOOGLE_APPLICATION_CREDENTIALS` (prod)

#### **Testing**
- [ ] Backend starts without errors: `uvicorn main:app`
- [ ] Farm creation works: `POST /farm`
- [ ] Intelligence endpoint returns BigQuery data: `GET /intelligence/{farm_id}`
- [ ] Firestore queries work: `gcloud firestore documents list --collection-id=farms`

---

## Common Issues & Troubleshooting

### "BigQuery table not found: agripulse_data.v_rainfall_7day"
**Cause:** BigQuery schema not created or view doesn't exist  
**Fix:** Run `bq query < infra/bigquery_schema.sql`

### "No data returned from BigQuery"
**Cause:** Tables created but not populated with data  
**Fix:** Run ingestion scripts:
```bash
cd ingestion && python weather_ingest.py && python market_ingest.py
```

### "Firestore permission denied"
**Cause:** Service account lacks `firestore.user` role  
**Fix:**
```bash
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member=serviceAccount:YOUR-SA@iam.gserviceaccount.com \
  --role=roles/firestore.user
```

### "AGRIPULSE_MOCK_DATA=0 but still getting mock data"
**Cause:** Process wasn't restarted, old config still cached  
**Fix:**
```bash
pkill -f "uvicorn"
# Then restart
uvicorn main:app --reload --port 8080
```

### "Farm data not persisting to Firestore"
**Cause:** Check `MOCK_MODE` evaluation in `backend/farm_store.py`  
**Debug:**
```python
# Add to farm_store.py line 21:
print(f"MOCK_MODE={MOCK_MODE}, AGRIPULSE_MOCK_DATA={os.environ.get('AGRIPULSE_MOCK_DATA')}")
```

---

## References

- BigQuery Schema: `infra/bigquery_schema.sql`
- Seed Data: `infra/synthetic_seed_data.sql`
- Agent SQL Queries: `agents/{weather,soil,market}_agent.py`
- GCP Client Setup: `ingestion/gcp_clients.py`
- Mock vs Prod Logic: `agents/bq_helper.py`, `backend/farm_store.py`
- Deployment: `infra/deploy.sh`
