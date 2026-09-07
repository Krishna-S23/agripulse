# ⚡ GCP Deployment Quick Reference (Cheat Sheet)

## 🎯 5-Minute Setup (For Those in a Hurry)

```bash
# 1. Create project & set default
gcloud projects create agripulse-prod
gcloud config set project agripulse-prod

# 2. Enable all APIs at once
gcloud services enable run.googleapis.com bigquery.googleapis.com \
  firestore.googleapis.com storage.googleapis.com aiplatform.googleapis.com \
  cloudbuild.googleapis.com cloudscheduler.googleapis.com logging.googleapis.com

# 3. Create buckets
gsutil mb -l us-central1 gs://agripulse-raw-agripulse-prod
gsutil mb -l us-central1 gs://agripulse-processed-agripulse-prod

# 4. Create BigQuery dataset & tables
bq query --use_legacy_sql=false < infra/bigquery_schema.sql

# 5. Create Firestore
gcloud firestore databases create --database=default --region=asia-south1 --type=firestore-native

# 6. Build & deploy to Cloud Run
gcloud builds submit --tag gcr.io/agripulse-prod/agripulse-backend:latest
gcloud run deploy agripulse-backend \
  --image gcr.io/agripulse-prod/agripulse-backend:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=agripulse-prod,AGRIPULSE_MOCK_DATA=0"

# 7. Get your live URL
gcloud run services describe agripulse-backend --region us-central1 --format='value(status.url)'
```

**Done! Your app is live.** ✨

---

## 📋 Copy-Paste Commands by Phase

### **Phase 1: Project Setup**

```bash
# Create project
gcloud projects create agripulse-prod --name="AgriPulse Production"
gcloud config set project agripulse-prod

# Enable APIs (all at once)
gcloud services enable run.googleapis.com bigquery.googleapis.com \
  firestore.googleapis.com storage.googleapis.com aiplatform.googleapis.com \
  cloudbuild.googleapis.com cloudscheduler.googleapis.com logging.googleapis.com

# Verify project ID
gcloud config list | grep project
```

---

### **Phase 2: Storage Setup**

```bash
# Create Cloud Storage buckets
gsutil mb -l us-central1 gs://agripulse-raw-agripulse-prod
gsutil mb -l us-central1 gs://agripulse-processed-agripulse-prod

# List buckets
gsutil ls

# Add bucket lifecycle rule (delete old files after 90 days)
gsutil lifecycle set - gs://agripulse-raw-agripulse-prod << 'EOF'
{
  "lifecycle": {
    "rule": [{
      "action": {"type": "Delete"},
      "condition": {"age": 90}
    }]
  }
}
EOF
```

---

### **Phase 3: BigQuery Setup**

```bash
# Create dataset & tables
cd agripulse-master
bq query --use_legacy_sql=false --project_id=agripulse-prod < infra/bigquery_schema.sql

# Load synthetic test data
bq query --use_legacy_sql=false --project_id=agripulse-prod < infra/synthetic_seed_data.sql

# Verify tables exist
bq ls --project_id=agripulse-prod agripulse_data

# Query a table
bq query --use_legacy_sql=false --project_id=agripulse-prod \
  "SELECT COUNT(*) as total FROM agripulse_data.farm"

# View schema
bq show --schema --format=prettyjson agripulse_data.farm
```

---

### **Phase 4: Firestore Setup**

```bash
# Create Firestore database
gcloud firestore databases create \
  --database=default \
  --region=asia-south1 \
  --type=firestore-native \
  --project=agripulse-prod

# List databases
gcloud firestore databases list --project=agripulse-prod

# Create security rules (optional)
gcloud firestore rules deploy infra/firestore.rules --project=agripulse-prod
```

---

### **Phase 5: Local Development**

```bash
# Authenticate locally
gcloud auth application-default login

# Set up .env
cp .env.example .env
# Edit .env and fill in:
# GCP_PROJECT_ID=agripulse-prod
# AGRIPULSE_MOCK_DATA=0

# Test local connection to BigQuery
gcloud bq ls

# Run backend locally
cd backend
uvicorn main:app --reload --port 8080

# In another terminal, test
curl http://localhost:8080/health
```

---

### **Phase 6: Containerization & Deployment**

```bash
# Build Docker image on Cloud
gcloud builds submit --tag gcr.io/agripulse-prod/agripulse-backend:latest

# View build logs
gcloud builds log --stream=true

# List images
gcloud container images list --project=agripulse-prod

# Deploy to Cloud Run
gcloud run deploy agripulse-backend \
  --image gcr.io/agripulse-prod/agripulse-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=agripulse-prod,BQ_DATASET=agripulse_data,AGRIPULSE_MOCK_DATA=0" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --project=agripulse-prod

# View service details
gcloud run services describe agripulse-backend --region=us-central1

# Get service URL
gcloud run services describe agripulse-backend \
  --region=us-central1 \
  --format='value(status.url)'
```

---

### **Phase 7: Testing Live Service**

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe agripulse-backend \
  --region=us-central1 \
  --format='value(status.url)')

echo "Your app is at: $SERVICE_URL"

# Test health endpoint
curl $SERVICE_URL/health

# Create a farm
curl -X POST $SERVICE_URL/farm \
  -H "Content-Type: application/json" \
  -d '{"district":"Coimbatore","crop":"Tomato","growth_stage":"Flowering"}'

# List farms
curl $SERVICE_URL/farms

# Get farm intelligence
curl $SERVICE_URL/intelligence/F628C03
```

---

### **Phase 8: Monitoring & Logs**

```bash
# View logs in real-time
gcloud run services logs read agripulse-backend \
  --limit 50 \
  --follow \
  --region us-central1

# View structured logs (JSON)
gcloud run services logs read agripulse-backend \
  --limit 10 \
  --region us-central1 \
  --format=json

# Get service metrics
gcloud run services describe agripulse-backend \
  --region=us-central1 \
  --format='value(status)'

# Set up error tracking (optional)
gcloud logging sinks create error-sink \
  logging.googleapis.com/projects/agripulse-prod/logs \
  --log-filter='severity=ERROR'
```

---

### **Phase 9: Data Ingestion**

```bash
# Authenticate for ingestion
gcloud auth application-default login

# Ingest weather data
cd ingestion
export GCP_PROJECT_ID=agripulse-prod
python weather_ingest.py

# Ingest market data (requires DATA_GOV_IN_API_KEY)
export DATA_GOV_IN_API_KEY=your-api-key
python market_ingest.py

# Verify ingestion
bq query --use_legacy_sql=false --project_id=agripulse-prod \
  "SELECT MAX(date) as latest_date FROM agripulse_data.weather"
```

---

### **Phase 10: Secrets Management**

```bash
# Create secret (store API key securely)
echo -n "your-api-key" | \
  gcloud secrets create data-gov-in-key \
  --data-file=- \
  --project=agripulse-prod

# Grant Cloud Run service account access to secret
gcloud secrets add-iam-policy-binding data-gov-in-key \
  --member=serviceAccount:agripulse-backend@appspot.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor \
  --project=agripulse-prod

# Deploy with secret
gcloud run deploy agripulse-backend \
  --image gcr.io/agripulse-prod/agripulse-backend:latest \
  --set-secrets DATA_GOV_IN_API_KEY=data-gov-in-key:latest \
  --region us-central1
```

---

### **Phase 11: Scheduling Daily Ingestion**

```bash
# Create Cloud Run Job for ingestion
gcloud run jobs create agripulse-ingest \
  --image gcr.io/agripulse-prod/agripulse-ingest:latest \
  --region us-central1 \
  --set-env-vars "GCP_PROJECT_ID=agripulse-prod,AGRIPULSE_MOCK_DATA=0" \
  --project=agripulse-prod

# Create Cloud Scheduler job to run it daily at 5 AM UTC
gcloud scheduler jobs create http agripulse-daily-ingest \
  --location us-central1 \
  --schedule "0 5 * * *" \
  --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/projects/agripulse-prod/locations/us-central1/jobs/agripulse-ingest:run" \
  --http-method POST \
  --oidc-service-account-email agripulse-scheduler@agripulse-prod.iam.gserviceaccount.com \
  --project=agripulse-prod
```

---

## 🔧 Useful One-Liners

```bash
# Get your project ID
PROJECT_ID=$(gcloud config get-value project)

# Get your service URL
SERVICE_URL=$(gcloud run services describe agripulse-backend --region=us-central1 --format='value(status.url)')

# Copy URL to clipboard (macOS)
gcloud run services describe agripulse-backend --region=us-central1 --format='value(status.url)' | pbcopy

# Delete everything (cleanup)
gcloud run services delete agripulse-backend --region us-central1 -q
bq rm -r -d agripulse_data
gsutil -m rm -r gs://agripulse-raw-${PROJECT_ID} gs://agripulse-processed-${PROJECT_ID}
gcloud firestore databases delete

# View all resources in project
gcloud compute resources list
```

---

## ❌ Common Errors & Quick Fixes

| Error                              | Fix                                                                                                           |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `API not enabled`                  | `gcloud services enable SERVICE-NAME.googleapis.com`                                                          |
| `Permission denied: BigQuery`      | `gcloud projects add-iam-policy-binding PROJECT --member=serviceAccount:... --role=roles/bigquery.dataEditor` |
| `Image not found`                  | `gcloud builds submit --tag gcr.io/PROJECT/APP:latest`                                                        |
| `Cloud Run service not found`      | Check region: `gcloud run services list --region=us-central1`                                                 |
| `Firestore not initialized`        | `gcloud firestore databases create --database=default`                                                        |
| `AGRIPULSE_MOCK_DATA not changing` | Redeploy: `gcloud run deploy SERVICE --set-env-vars AGRIPULSE_MOCK_DATA=0`                                    |

---

## 📊 Monitoring Commands

```bash
# Check service status
gcloud run services describe agripulse-backend --region=us-central1

# View recent deployments
gcloud run revisions list --service=agripulse-backend --region=us-central1

# Check quotas & usage
gcloud compute project-info describe --project=agripulse-prod

# View billing
gcloud billing accounts list
gcloud compute billing-accounts get-iam-policy BILLING-ACCOUNT-ID
```

---

## 🎯 Environment Variables Quick Reference

```env
# Required
GCP_PROJECT_ID=agripulse-prod

# GCP Defaults (can customize)
GCP_REGION=us-central1
BQ_DATASET=agripulse_data
RAW_BUCKET=agripulse-raw-agripulse-prod
PROCESSED_BUCKET=agripulse-processed-agripulse-prod

# Mode (0 = production, 1 = mock)
AGRIPULSE_MOCK_DATA=0

# AI Model
VERTEX_AI_MODEL=gemini-2.0-flash

# External APIs
DATA_GOV_IN_API_KEY=your-key

# API Settings
CORS_ORIGINS=*
```

---

## 📞 Getting Help

```bash
# Help on a command
gcloud run --help
gcloud run deploy --help

# Open GCP console in browser
gcloud console projects describe agripulse-prod

# Check gcloud version
gcloud --version

# Update gcloud
gcloud components update
```

---

**Remember:** Save this file! You'll reference it constantly. 🚀
