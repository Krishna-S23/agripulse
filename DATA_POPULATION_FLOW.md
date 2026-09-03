# 📊 How AgriPulse Tables Get Populated

## Quick Answer

The `bigquery_schema.sql` **creates EMPTY tables**. Data gets populated by:

1. **Ingestion scripts** (pull data from external sources)
2. **API writes** (users create farms via web app)
3. **Seed data** (for testing)

---

## 🔄 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL DATA SOURCES                        │
├─────────────┬──────────────┬──────────────┬─────────────┬──────────┤
│   NASA      │  Open-Meteo  │ data.gov.in  │   Firestore │  Manual  │
│   POWER     │  (Forecast)  │  (Agmarknet) │  (Web App)  │  CSV     │
└──────┬──────┴──────┬───────┴──────┬───────┴──────┬──────┴────┬─────┘
       │             │              │              │           │
       │ Python      │ Python       │ Python       │ Python    │ Python
       │ script      │ script       │ script       │ script    │ script
       ▼             ▼              ▼              ▼           ▼
    ┌──────────────────────────────────────────────────────────────┐
    │              CSV Files (Temporary)                           │
    │  • weather_latest.csv                                       │
    │  • market_prices_latest.csv                                 │
    │  • crop_history_clean.csv                                   │
    │  (Store in /tmp/ locally, then upload)                      │
    └────────┬───────────────────────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────────────────────────┐
    │         Google Cloud Storage (GCS)                           │
    │  • gs://agripulse-raw/weather/2026-09-03.csv               │
    │  • gs://agripulse-processed/weather/2026-09-03.csv         │
    │  • gs://agripulse-processed/market_prices/2026-09-03.csv   │
    │  (Staging area before BigQuery)                             │
    └────────┬───────────────────────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────────────────────────┐
    │              BIGQUERY DATASET                                │
    │            (agripulse_data)                                 │
    ├──────────────────────────────────────────────────────────────┤
    │  Tables (RAW DATA):                                         │
    │  ├─ farm (from web app / Firestore)                         │
    │  ├─ weather (from NASA POWER + Open-Meteo)                  │
    │  ├─ market_prices (from data.gov.in Agmarknet)              │
    │  ├─ soil_conditions (synthetic test data)                   │
    │  └─ crop_history (from data.gov.in CSV)                     │
    │                                                              │
    │  Views (AGGREGATED):                                        │
    │  ├─ v_rainfall_7day (7-day rolling avg)                     │
    │  ├─ v_latest_soil (most recent reading/farm)                │
    │  ├─ v_weekly_price_trend (weekly aggregation)               │
    │  └─ v_yield_trend (year-over-year)                          │
    └────────┬───────────────────────────────────────────────────┘
             │
             ▼
        AGENTS QUERY
     ┌──────────────────┐
     │ Weather Agent    │────→ Reads v_rainfall_7day
     │ Soil Agent       │────→ Reads v_latest_soil
     │ Market Agent     │────→ Reads v_weekly_price_trend
     └──────────────────┘
             │
             ▼
        RECOMMENDATIONS
     ("Irrigate Now", "Sell Now", etc.)
```

---

## 📋 Table-by-Table Population Guide

### **1. FARM Table** (Created by Users via Web App)

**Location:** `agripulse_data.farm`

**Who populates it:**
- Backend API endpoint `/farm` (POST request)
- Users create farms via React UI
- Data written to Firestore first, then mirrored to BigQuery

**Population Flow:**
```
User fills form in React UI
    ↓
Sends POST /farm request
    ↓
backend/main.py:create_farm()
    ↓
Saves to Firestore (primary storage)
    ↓
[Optional] Mirror to BigQuery for analytics
    ↓
Table now has 1 more row
```

**Example:**
```python
# User submits via UI
curl -X POST http://localhost:8080/farm \
  -H "Content-Type: application/json" \
  -d '{
    "district": "Coimbatore",
    "crop": "Tomato",
    "growth_stage": "Flowering",
    "area_acres": 2.5,
    "owner_name": "Farmer John"
  }'

# This triggers:
# 1. Firestore: Creates document farms/F628C03 with the data
# 2. BigQuery: Inserts row into agripulse_data.farm table
```

**Verify data populated:**
```bash
bq query "SELECT COUNT(*) FROM agripulse_data.farm"
# Output: 1 (or more if multiple farms created)
```

---

### **2. WEATHER Table** (From NASA POWER & Open-Meteo)

**Location:** `agripulse_data.weather`

**Who populates it:**
- `ingestion/weather_ingest.py` script
- Runs manually or scheduled daily

**Population Flow:**
```
ingestion/weather_ingest.py runs
    ↓
For each district (Coimbatore, Erode, Salem):
    ├─ Fetch historical 30 days from NASA POWER API
    │  └─ Returns: temp_c, rainfall_mm, humidity_pct
    ├─ Fetch forecast 3 days from Open-Meteo API
    │  └─ Returns: temp, rain_prob_pct
    └─ Combine into one row per day per district
    ↓
Write to CSV: /tmp/weather_latest.csv
    ↓
Upload to GCS: gs://agripulse-processed/weather/2026-09-03.csv
    ↓
Load CSV into BigQuery table: agripulse_data.weather
    ↓
Table now has 6 more rows (3 districts × 2 days)
```

**Step-by-step code flow:**

```python
# From weather_ingest.py

# Step 1: Fetch NASA historical data
rows = fetch_nasa_power_history("Coimbatore", 11.0168, 76.9558, days_back=30)
# Returns:
# [
#   {date: "2026-08-03", district: "Coimbatore", temperature_c: 28.4, ...},
#   {date: "2026-08-04", district: "Coimbatore", temperature_c: 29.1, ...},
#   ... (30 rows)
# ]

# Step 2: Fetch Open-Meteo forecast
forecast_rows = fetch_open_meteo_forecast("Coimbatore", 11.0168, 76.9558, days_ahead=3)
# Returns:
# [
#   {date: "2026-09-03", district: "Coimbatore", rain_prob_pct: 75, ...},
#   {date: "2026-09-04", district: "Coimbatore", rain_prob_pct: 60, ...},
#   {date: "2026-09-05", district: "Coimbatore", rain_prob_pct: 40, ...}
# ]

# Step 3: Repeat for Erode and Salem (3 districts total)
# Step 4: Combine all rows
all_rows = rows + forecast_rows + erode_rows + salem_rows

# Step 5: Write to CSV file
write_csv(all_rows, "/tmp/weather_latest.csv")
# File contains: 33 districts × 3 = ~99 rows

# Step 6: Upload to Cloud Storage
gcs_path = upload_to_gcs("/tmp/weather_latest.csv", 
                         PROCESSED_BUCKET, 
                         "weather/2026-09-03.csv")
# File now at: gs://agripulse-processed/weather/2026-09-03.csv

# Step 7: Load CSV into BigQuery
load_csv_to_bq(gcs_path, "agripulse_data.weather")
# BigQuery executes: LOAD DATA FROM 'gs://...' INTO agripulse_data.weather
```

**Run the ingestion:**
```bash
cd ingestion
python weather_ingest.py

# Output:
# INFO: Fetching historical weather for Coimbatore
# INFO: Fetching forecast for Coimbatore
# INFO: Fetching historical weather for Erode
# INFO: Fetching forecast for Erode
# ... (repeats for Salem)
# INFO: Wrote 99 rows to /tmp/weather_latest.csv
# INFO: Uploaded to gs://agripulse-processed/weather/2026-09-03.csv
# INFO: Loaded into agripulse_data.weather
```

**Verify data populated:**
```bash
bq query "SELECT COUNT(*) FROM agripulse_data.weather"
# Output: 99 (3 districts × 33 days)

bq query "SELECT DISTINCT district FROM agripulse_data.weather ORDER BY district"
# Output:
# Coimbatore
# Erode
# Salem
```

---

### **3. MARKET_PRICES Table** (From data.gov.in Agmarknet)

**Location:** `agripulse_data.market_prices`

**Who populates it:**
- `ingestion/market_ingest.py` script
- Requires API key from https://data.gov.in

**Population Flow:**
```
ingestion/market_ingest.py runs
    ↓
For each crop (Tomato, Onion):
    └─ Call data.gov.in API with filters:
       • state = "Tamil Nadu"
       • commodity = "Tomato" (or "Onion")
       └─ Returns latest market prices
    ↓
Filter results to target districts only
    ├─ Keep: Coimbatore, Erode, Salem
    └─ Discard: other districts
    ↓
Write to CSV: /tmp/market_prices_latest.csv
    ↓
Upload to GCS: gs://agripulse-processed/market_prices/2026-09-03.csv
    ↓
Load CSV into BigQuery table: agripulse_data.market_prices
    ↓
Table now has ~12 new rows (2 crops × 3 districts × 2 price points)
```

**Step-by-step code flow:**

```python
# From market_ingest.py

# Step 1: Fetch Tomato prices
tomato_rows = fetch_prices("Tomato")
# API call to: https://api.data.gov.in/resource/9ef84268...?api_key=...&commodity=Tomato
# Returns:
# [
#   {date: "2026-09-01", crop: "Tomato", market: "Coimbatore", 
#    district: "Coimbatore", modal_price: 2100, min_price: 1950, max_price: 2250},
#   {date: "2026-09-01", crop: "Tomato", market: "Erode", 
#    district: "Erode", modal_price: 2250, ...},
#   ... (more markets)
# ]

# Step 2: Fetch Onion prices
onion_rows = fetch_prices("Onion")
# Returns similar structure for onion

# Step 3: Combine
all_rows = tomato_rows + onion_rows

# Step 4: Write to CSV
write_csv(all_rows, "/tmp/market_prices_latest.csv")

# Step 5: Upload to GCS
upload_to_gcs("/tmp/market_prices_latest.csv", 
              PROCESSED_BUCKET, 
              "market_prices/2026-09-03.csv")

# Step 6: Load into BigQuery
load_csv_to_bq(gcs_path, "agripulse_data.market_prices")
```

**Run the ingestion:**
```bash
export DATA_GOV_IN_API_KEY=your-api-key  # Get from data.gov.in
cd ingestion
python market_ingest.py

# Output:
# INFO: Fetching prices for Tomato
# INFO: Found 47 records for Tamil Nadu
# INFO: Filtered to 3 target districts: 6 rows
# INFO: Fetching prices for Onion
# INFO: Found 52 records for Tamil Nadu
# INFO: Filtered to 3 target districts: 6 rows
# INFO: Wrote 12 rows to /tmp/market_prices_latest.csv
# INFO: Loaded into agripulse_data.market_prices
```

**Verify data populated:**
```bash
bq query "SELECT COUNT(*) FROM agripulse_data.market_prices"
# Output: 12 (varies by crop/district count)

bq query "SELECT DISTINCT crop FROM agripulse_data.market_prices"
# Output: Tomato, Onion
```

---

### **4. SOIL_CONDITIONS Table** (Synthetic Test Data)

**Location:** `agripulse_data.soil_conditions`

**Who populates it:**
- `infra/synthetic_seed_data.sql` (one-time seed)
- Manually generated for MVP (no real sensors yet)

**Population Flow:**
```
Developer runs: bq query < infra/synthetic_seed_data.sql
    ↓
SQL script generates synthetic soil readings
    ↓
45 farms × 10 days × random readings = 450 rows
    ↓
Table populated with test data
```

**Example from synthetic_seed_data.sql:**
```sql
-- Insert synthetic soil data for testing
INSERT INTO `agripulse_data.soil_conditions`
  (farm_id, date, moisture, ph, nitrogen)
VALUES
  ('F001', '2026-08-20', 61.4, 6.7, 'Adequate'),
  ('F001', '2026-08-21', 60.2, 6.8, 'Adequate'),
  ('F002', '2026-08-20', 38.2, 6.2, 'Low'),
  -- ... (450 total rows)
```

**Run seed data:**
```bash
bq query --use_legacy_sql=false < infra/synthetic_seed_data.sql

# Output:
# Inserted 450 rows into agripulse_data.soil_conditions
```

---

### **5. CROP_HISTORY Table** (Annual Production Data)

**Location:** `agripulse_data.crop_history`

**Who populates it:**
- `ingestion/crop_history_ingest.py` script
- Manual CSV download from data.gov.in first

**Population Flow:**
```
1. Download CSV from data.gov.in manually:
   "District-wise, Season-wise Crop Production Statistics"
   └─ Save as crop_production.csv
    ↓
2. Run: python crop_history_ingest.py
    ↓
3. Script reads CSV and transforms:
   ├─ Keep only target districts (Coimbatore, Erode, Salem)
   ├─ Keep only target crops (Tomato, Onion)
   └─ Calculate: yield = production / area
    ↓
4. Write to /tmp/crop_history_clean.csv
    ↓
5. Upload to GCS: gs://agripulse-processed/crop_history/2026-09-03.csv
    ↓
6. Load into BigQuery (with WRITE_TRUNCATE = replace existing)
    ↓
Table updated with annual production data
```

**Run crop history ingestion:**
```bash
# First, download CSV from data.gov.in and save locally

cd ingestion
RAW_CSV_PATH=~/Downloads/crop_production.csv python crop_history_ingest.py

# Output:
# INFO: Reading crop_production.csv
# INFO: Processing 1500 rows, filtering to target districts/crops
# INFO: Found 120 relevant records
# INFO: Wrote 120 rows to /tmp/crop_history_clean.csv
# INFO: Loaded into agripulse_data.crop_history (REPLACE mode)
```

---

## 🔍 Views - The Aggregated Layer

**Views are NOT populated separately.** They are **queries that aggregate raw tables**.

### Example: v_rainfall_7day View

**Raw Data:** `weather` table
```
date       | district     | rainfall_mm
-----------|--------------|----
2026-08-28 | Coimbatore   | 5.2
2026-08-29 | Coimbatore   | 8.1
2026-08-30 | Coimbatore   | 12.4
2026-08-31 | Coimbatore   | 3.2
2026-09-01 | Coimbatore   | 18.2
2026-09-02 | Coimbatore   | 22.5
2026-09-03 | Coimbatore   | 15.3
```

**View Query (v_rainfall_7day):**
```sql
SELECT
  district,
  date,
  rainfall_mm,
  temperature_c,
  humidity_pct,
  AVG(rainfall_mm) OVER (
    PARTITION BY district ORDER BY UNIX_DATE(date)
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS rainfall_7day_avg
FROM `agripulse_data.weather`
```

**Result (computed on-the-fly):**
```
date       | district     | rainfall_mm | rainfall_7day_avg
-----------|--------------|-------------|------------------
2026-08-28 | Coimbatore   | 5.2         | 5.2 (only 1 day)
2026-08-29 | Coimbatore   | 8.1         | 6.65 (avg of 2 days)
2026-08-30 | Coimbatore   | 12.4        | 8.57 (avg of 3 days)
...
2026-09-03 | Coimbatore   | 15.3        | 12.43 (avg of 7 days)
```

**When Weather Agent queries this:**
```python
# agents/weather_agent.py
rows = run_query(SQL, {"district": "Coimbatore", "mock_key": "weather"})
# Returns the view result, showing:
# - Latest rainfall (15.3 mm)
# - 7-day average (12.43 mm)
# - Used to decide if rainfall is "above average" (spike)
```

---

## 🔄 Complete Data Lifecycle Timeline

```
Day 1 (Initial Setup):
  ├─ Run: bq query < infra/bigquery_schema.sql
  │  └─ Creates empty tables + views
  └─ Run: bq query < infra/synthetic_seed_data.sql
     └─ Populates farm (45) and soil_conditions (450) with test data

Day 2 (First Ingestion):
  ├─ Run: python weather_ingest.py
  │  └─ Populates weather table (~100 rows)
  ├─ Run: python market_ingest.py
  │  └─ Populates market_prices table (~12 rows)
  └─ User creates a farm via UI
     └─ Populates farm table with 1 new row

Day 3+:
  ├─ User creates more farms
  │  └─ farm table grows
  ├─ Daily scheduled ingestion (Cloud Scheduler)
  │  ├─ weather table gets updated (new 3-6 rows per day)
  │  ├─ market_prices table gets updated
  │  └─ Views automatically reflect new data
  └─ Agents query views
     └─ Always see latest aggregated data
```

---

## 🚀 How to Populate Your Own Tables

### Scenario 1: Quick Test (Use Synthetic Data)

```bash
# Create empty tables
bq query --use_legacy_sql=false < infra/bigquery_schema.sql

# Populate with synthetic test data (45 farms, 450 soil readings)
bq query --use_legacy_sql=false < infra/synthetic_seed_data.sql

# Verify
bq query "SELECT COUNT(*) FROM agripulse_data.farm"
# Output: 45 ✅
```

**Time:** 30 seconds  
**Data quality:** Test-only, not realistic

---

### Scenario 2: Real Weather Data (Recommended)

```bash
# Create tables (as above)
bq query --use_legacy_sql=false < infra/bigquery_schema.sql
bq query --use_legacy_sql=false < infra/synthetic_seed_data.sql

# Ingest real weather
cd ingestion
python weather_ingest.py

# Verify
bq query "SELECT MAX(date) FROM agripulse_data.weather"
# Output: 2026-09-03 ✅
```

**Time:** 2 minutes  
**Data quality:** Real (NASA + Open-Meteo)

---

### Scenario 3: Full Real Data

```bash
# Create tables
bq query --use_legacy_sql=false < infra/bigquery_schema.sql
bq query --use_legacy_sql=false < infra/synthetic_seed_data.sql

# Get API key from https://data.gov.in
export DATA_GOV_IN_API_KEY=your-key

# Ingest all data
cd ingestion
python weather_ingest.py
python market_ingest.py
RAW_CSV_PATH=~/Downloads/crop_production.csv python crop_history_ingest.py

# Create farms via UI (or API)
curl -X POST http://localhost:8080/farm \
  -H "Content-Type: application/json" \
  -d '{"district":"Coimbatore","crop":"Tomato"}'

# Verify all tables populated
bq query "SELECT 'farm' as tbl, COUNT(*) as cnt FROM agripulse_data.farm
          UNION ALL
          SELECT 'weather', COUNT(*) FROM agripulse_data.weather
          UNION ALL
          SELECT 'market_prices', COUNT(*) FROM agripulse_data.market_prices
          UNION ALL
          SELECT 'soil_conditions', COUNT(*) FROM agripulse_data.soil_conditions"
# Output:
# tbl              | cnt
# farm             | 46
# weather          | 99
# market_prices    | 12
# soil_conditions  | 450
```

**Time:** 5-10 minutes  
**Data quality:** Production-ready

---

## 📈 Monitoring Table Growth

```bash
# View table sizes
bq ls --project_id=agripulse-prod -t -d agripulse_data

# Get detailed stats
bq show --project_id=agripulse-prod \
  --format=prettyjson agripulse_data.weather | jq '.numRows, .numBytes'

# Monitor ingestion progress
bq query --use_legacy_sql=false \
  "SELECT table_name, row_count, size_bytes 
   FROM agripulse_data.__TABLES__
   ORDER BY row_count DESC"
```

---

## 🎯 Key Takeaways

| Table | Data Source | How It's Populated | Update Frequency | Purpose |
|-------|-------------|-------------------|-----------------|---------|
| **farm** | Web API + Firestore | Users create via UI | Real-time | Farm registry |
| **weather** | NASA POWER + Open-Meteo | Python script `weather_ingest.py` | Daily (scheduled) | Weather signals |
| **market_prices** | data.gov.in Agmarknet | Python script `market_ingest.py` | Daily (scheduled) | Market prices |
| **soil_conditions** | Synthetic generator | `synthetic_seed_data.sql` | One-time (MVP) | Soil signals |
| **crop_history** | data.gov.in CSV | Python script `crop_history_ingest.py` | Annually | Yield trends |
| **Views** | Other tables | SQL queries (computed) | Real-time (from source) | Aggregations |

---

## 🔗 Related Files

- **Schema creation:** `infra/bigquery_schema.sql` (creates tables)
- **Ingestion scripts:** `ingestion/weather_ingest.py`, `ingestion/market_ingest.py`, `ingestion/crop_history_ingest.py`
- **Test data:** `infra/synthetic_seed_data.sql`
- **GCP helpers:** `ingestion/gcp_clients.py` (handles uploads + loads)
- **Backend writes:** `backend/farm_store.py` (writes farms to Firestore/BigQuery)

