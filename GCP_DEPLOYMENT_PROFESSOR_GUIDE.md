# 🎓 GCP Deployment Mastery: AgriPulse Edition
## A Professor's Guide to Cloud Native Development

---

## 📚 Table of Contents
1. [Foundations: Understanding GCP](#foundations)
2. [Phase 1: Project Setup](#phase-1-project-setup)
3. [Phase 2: Local Development with GCP](#phase-2-local-development)
4. [Phase 3: Database & Data Pipeline](#phase-3-database--data-pipeline)
5. [Phase 4: Containerization & Cloud Run](#phase-4-containerization--cloud-run)
6. [Phase 5: Going Live with a Shareable URL](#phase-5-going-live)
7. [Troubleshooting & Best Practices](#troubleshooting)

---

## 🏗️ Foundations: Understanding GCP

### What You Need to Know First

Before we start, let's understand the **three pillars** of what you're about to build:

#### **Pillar 1: Compute** (Where your app runs)
- **Cloud Run**: Serverless container platform
  - You upload a Docker container
  - GCP runs it automatically
  - You pay only when it's being used
  - Scales from 0 → millions of requests
  - **Best for**: Web APIs, scheduled jobs, microservices

#### **Pillar 2: Data** (Where your data lives)
- **BigQuery**: Data warehouse (SQL queries on massive datasets)
  - Stores weather, market, soil data
  - Fast analytics queries
  - Pay per GB scanned (not stored)
  
- **Firestore**: NoSQL database (stores farm profiles)
  - Document-based (like MongoDB)
  - Real-time updates
  - Good for structured data like farm records

#### **Pillar 3: AI** (Intelligence)
- **Vertex AI**: Google's unified AI platform
  - Access to Gemini models
  - Authentication is built-in (no API keys!)
  - Integrates with GCP services

### Architecture Diagram (Mental Model)

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET (Users)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼ (Your shareable URL)
                    ┌────────────────────┐
                    │   Cloud Run        │ ◄─── Runs your app
                    │ (agripulse-backend)│     (Docker container)
                    └────────┬───────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────┐      ┌────────────┐
    │BigQuery  │      │Firestore │      │ Vertex AI  │
    │(Weather, │      │ (Farms)  │      │ (Gemini)   │
    │ Market,  │      │          │      │            │
    │ Soil)    │      │          │      │            │
    └──────────┘      └──────────┘      └────────────┘
         ▲
         │ (Data ingestion)
         │
    ┌────────────────────────────────────────────┐
    │  External APIs (NASA, Open-Meteo, etc.)    │
    └────────────────────────────────────────────┘
```

### Key Concepts You'll Encounter

| Concept | What It Means | Example |
|---------|--------------|---------|
| **Project** | Container for all your GCP resources | "agripulse-prod" |
| **Service Account** | Robot user that services use to authenticate | Used by Cloud Run to access BigQuery |
| **IAM (Identity & Access Management)** | Who can do what | "Cloud Run service account can read BigQuery" |
| **Region** | Geographic location where your data/compute lives | `us-central1` (Iowa) |
| **API** | A Google service you can call | BigQuery API, Storage API |
| **Billing Account** | Where charges go | Your credit card |

---

## 🚀 Phase 1: Project Setup

### Step 1.1: Create a GCP Account & Project

#### If you don't have a GCP account:
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **Sign In** → Use your Google account
3. Google will offer you a **free trial** ($300 credit for 90 days) ✅

#### Create your project:
1. In the top-left, click **Select a Project**
2. Click **NEW PROJECT**
3. Fill in:
   - **Project name**: `agripulse-prod` (or your preferred name)
   - **Location**: Leave as "Organization" (or create new if prompted)
4. Click **CREATE**
5. Wait 30 seconds for the project to initialize

**What Just Happened?**
You've created a **sandbox** where all your resources will live. Think of it like getting your own office building in a cloud datacenter.

---

### Step 1.2: Enable Required APIs

APIs are like "permissions" to use Google services. Your app needs permission to:
- Store data in BigQuery
- Store files in Cloud Storage
- Use Firestore
- Use Vertex AI
- Run containers in Cloud Run
- etc.

**Enable via Console (GUI):**

1. In the GCP console, search for **"APIs & Services"** → **Library**
2. Enable these one by one (search each, click **ENABLE**):

| API Name | Why You Need It |
|----------|---|
| Cloud Run API | Deploy your Docker container |
| BigQuery API | Store & query weather/market/soil data |
| Firestore API | Store farm profiles |
| Cloud Storage API | Store raw/processed data files |
| Vertex AI API | Call Gemini models |
| Cloud Build API | Build Docker images |
| Cloud Scheduler API | Schedule daily ingestion jobs |
| Cloud Logging API | View application logs |

**Enable via Command Line (gcloud CLI - Faster):**

```bash
gcloud services enable \
  run.googleapis.com \
  bigquery.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  logging.googleapis.com \
  --project=agripulse-prod
```

**What Just Happened?**
You've flipped the "on" switch for the services your application needs. Without enabling these, Cloud Run wouldn't be able to call BigQuery, etc.

---

### Step 1.3: Set Up Billing (Important!)

Even with free tier limits, you need billing enabled.

1. Go to **Billing** (left sidebar)
2. Click **Link a Billing Account**
3. Select your payment method
4. You'll get **$300 free credit** for 90 days

**Cost Estimate for AgriPulse:**
- Cloud Run: ~$0.20/day (for testing)
- BigQuery: ~$0.50/day (queries on ~50GB data)
- Firestore: ~$0.05/day (light usage)
- **Monthly estimate**: $20-30 (within free tier for first 90 days)

---

### Step 1.4: Install & Configure gcloud CLI

The **gcloud CLI** is your command-line interface to GCP. It's like SSH for your cloud.

#### Install gcloud:
**macOS (using Homebrew):**
```bash
brew install google-cloud-sdk
```

**Linux/Ubuntu:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

**Windows:**
Download installer from [cloud.google.com/sdk](https://cloud.google.com/sdk)

#### Initialize gcloud:
```bash
gcloud init
```

Follow the prompts:
1. Sign in with your Google account
2. Select your project: `agripulse-prod`
3. Accept region suggestion

#### Verify installation:
```bash
gcloud --version
gcloud config list
```

**What Just Happened?**
You've installed a command-line tool that lets you control GCP without clicking the web console. This is how professionals work.

---

### Step 1.5: Create Cloud Storage Buckets

Buckets are folders in the cloud. Think of them as AWS S3 buckets.

```bash
# Set your project ID
export PROJECT_ID=agripulse-prod

# Create raw data bucket (stores data as-is from APIs)
gsutil mb -l us-central1 gs://agripulse-raw-${PROJECT_ID}

# Create processed data bucket (stores cleaned data before BigQuery)
gsutil mb -l us-central1 gs://agripulse-processed-${PROJECT_ID}

# Verify buckets created
gsutil ls
```

**Output should be:**
```
gs://agripulse-raw-agripulse-prod/
gs://agripulse-processed-agripulse-prod/
```

**What Just Happened?**
You've created two folders in the cloud where your data ingestion pipeline will store files before loading them into BigQuery.

---

## 💾 Phase 2: Local Development with GCP

### Step 2.1: Configure Your Local Environment

In your project root, create/edit `.env`:

```bash
cp .env.example .env
```

Fill in `.env`:
```env
# GCP Configuration
GCP_PROJECT_ID=agripulse-prod
GCP_REGION=us-central1
BQ_DATASET=agripulse_data
RAW_BUCKET=agripulse-raw-agripulse-prod
PROCESSED_BUCKET=agripulse-processed-agripulse-prod

# Switch to production mode (reads from BigQuery)
AGRIPULSE_MOCK_DATA=0

# Vertex AI
VERTEX_AI_MODEL=gemini-2.0-flash

# External APIs (get these separately)
DATA_GOV_IN_API_KEY=your-actual-key-here

# Frontend
CORS_ORIGINS=*
```

---

### Step 2.2: Authenticate Locally with gcloud

When running locally, you need to tell gcloud "this is me" so it can access BigQuery, Firestore, etc.

```bash
# Login with your Google account
gcloud auth application-default login
```

This opens your browser. Click **Allow** to grant permissions.

**What Just Happened?**
You've created a **local credentials file** (usually `~/.config/gcloud/`) that allows your laptop to access GCP services as if it were running in the cloud.

---

### Step 2.3: Test GCP Connection Locally

```bash
# Test BigQuery connection
gcloud bq ls

# Test Firestore (you'll set it up next)
gcloud firestore databases list

# Test Cloud Storage
gsutil ls gs://agripulse-raw-${PROJECT_ID}
```

If these work, your local authentication is set up correctly! ✅

---

## 🗄️ Phase 3: Database & Data Pipeline

### Step 3.1: Create BigQuery Dataset & Tables

The schema file (`infra/bigquery_schema.sql`) defines your tables.

```bash
# Create the dataset and all tables
cd agripulse-master
bq query --use_legacy_sql=false --project_id=agripulse-prod < infra/bigquery_schema.sql

# Verify dataset created
bq ls agripulse_data

# Verify tables
bq ls agripulse_data --tables
```

**Expected Output:**
```
  farm
  weather
  soil_conditions
  market_prices
  crop_history
  v_rainfall_7day (view)
  v_latest_soil (view)
  v_weekly_price_trend (view)
  v_yield_trend (view)
```

**Key Concepts:**
- **Tables**: Raw data storage
- **Views**: Virtual tables (defined by queries on other tables)
  - `v_rainfall_7day`: Weekly weather rolling window
  - `v_latest_soil`: Most recent soil reading per farm
  - `v_weekly_price_trend`: Market prices aggregated weekly

---

### Step 3.2: Seed Initial Data (Optional but Recommended)

```bash
# Load synthetic farm + soil data (for testing)
bq query --use_legacy_sql=false --project_id=agripulse-prod < infra/synthetic_seed_data.sql

# Verify data loaded
bq query --use_legacy_sql=false "SELECT COUNT(*) FROM agripulse_data.farm" --project_id=agripulse-prod
# Output: 45 farms

bq query --use_legacy_sql=false "SELECT COUNT(*) FROM agripulse_data.soil_conditions" --project_id=agripulse-prod
# Output: 450 soil readings
```

**What Just Happened?**
You've populated your database with synthetic test data. This is useful for development so you don't need real data immediately.

---

### Step 3.3: Create Firestore Database

Firestore stores farm profile documents (created by users).

```bash
# Create Firestore database in Native mode, asia-south1 region
gcloud firestore databases create \
  --database=default \
  --region=asia-south1 \
  --type=firestore-native \
  --project=agripulse-prod
```

(If it asks "Do you want to delete the Datastore database?", click **DELETE**)

**Verify creation:**
```bash
gcloud firestore databases list --project=agripulse-prod
```

**What Just Happened?**
Firestore is now ready to store farm documents. When users create a farm in the web app, it gets saved here.

---

### Step 3.4: Ingest Real Weather Data

The ingestion pipeline pulls data from external APIs (NASA, Open-Meteo, Agmarknet).

**Note:** This step is optional for testing. You can use synthetic data first.

```bash
cd ingestion

# Install dependencies if needed
pip install -r ../requirements.txt

# Ingest weather (NASA historical + Open-Meteo forecast)
export GCP_PROJECT_ID=agripulse-prod
python weather_ingest.py

# Ingest market prices (requires DATA_GOV_IN_API_KEY)
# First, get your API key from https://data.gov.in
export DATA_GOV_IN_API_KEY=your-key
python market_ingest.py
```

**Verify data ingested:**
```bash
bq query "SELECT COUNT(*) FROM agripulse_data.weather" --project_id=agripulse-prod
bq query "SELECT COUNT(*) FROM agripulse_data.market_prices" --project_id=agripulse-prod
```

---

## 🐳 Phase 4: Containerization & Cloud Run

### What is Containerization?

**Problem:** Your app works on your laptop. How do you guarantee it works the same way in the cloud?

**Solution:** Docker. It packages your app with all dependencies into a container.

Think of it like:
- Your laptop = shipping your desk + computer + all files
- Docker = shipping a sealed box with everything pre-configured

### Step 4.1: Understand the Dockerfile

The project already has a `Dockerfile`. Let's understand it:

```dockerfile
FROM python:3.11-slim                    # Start with Python 3.11
WORKDIR /app                              # Set working directory
COPY requirements.txt .                   # Copy dependency list
RUN pip install -r requirements.txt      # Install dependencies
COPY . .                                  # Copy all code
EXPOSE 8080                               # Listen on port 8080
CMD ["uvicorn", "backend/main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**What This Does:**
1. Starts with a lightweight Python image
2. Installs your dependencies
3. Copies your code
4. Runs your FastAPI app on port 8080

---

### Step 4.2: Build Docker Image Locally (Optional, for testing)

```bash
# Build the image locally
docker build -t agripulse:latest .

# Test it locally
docker run -p 8080:8080 \
  -e AGRIPULSE_MOCK_DATA=1 \
  agripulse:latest

# Visit http://localhost:8080
```

---

### Step 4.3: Build & Push to Cloud (Cloud Build)

Cloud Build is GCP's CI/CD service. It:
1. Takes your code
2. Builds the Docker image
3. Pushes it to Container Registry
4. Automatically deploys to Cloud Run

**Build on Cloud (this does all the work for you):**

```bash
# Build and push image to GCP Container Registry
gcloud builds submit \
  --tag gcr.io/agripulse-prod/agripulse-backend:latest \
  --project agripulse-prod

# This will:
# 1. Upload your code to GCP
# 2. Build the Docker image (in the cloud)
# 3. Push to Container Registry (gcr.io)
# 4. Print the image path when done
```

**Watch the build:**
```bash
# See build status in real-time
gcloud builds log --stream=true

# Or view in console:
# https://console.cloud.google.com/cloud-build/builds
```

**What Just Happened?**
Your code is now packaged as a Docker image and stored in GCP's container registry. Think of it like uploading a .zip file of your entire application.

---

### Step 4.4: Deploy to Cloud Run

Cloud Run takes your Docker image and runs it on the cloud.

```bash
# Deploy the image
gcloud run deploy agripulse-backend \
  --image gcr.io/agripulse-prod/agripulse-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=agripulse-prod,BQ_DATASET=agripulse_data,AGRIPULSE_MOCK_DATA=0" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --project agripulse-prod
```

**Flags explained:**
- `--image`: Which Docker image to run
- `--platform managed`: Fully managed (you don't manage servers)
- `--region us-central1`: Where to run (Iowa datacenter)
- `--allow-unauthenticated`: Anyone can call your API (no auth needed)
- `--set-env-vars`: Pass environment variables
- `--memory 512Mi`: RAM allocated
- `--cpu 1`: CPU cores
- `--timeout 300`: Request timeout in seconds

**Expected Output:**
```
Deploying container to Cloud Run service [agripulse-backend] in [us-central1]...
✓ Deploying new service...
✓ Creating Revision...
✓ Routing traffic...
✓ Setting IAM Policy...
Done.
Service [agripulse-backend] revision [agripulse-backend-00001-abc] has been deployed and is serving 100 percent of traffic at:
https://agripulse-backend-a1b2c3d4-uc.a.run.app
```

**That URL is your shareable link!** 🎉

---

## 📍 Phase 5: Going Live with a Shareable URL

### Step 5.1: Test Your Live Deployment

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe agripulse-backend \
  --platform managed \
  --region us-central1 \
  --format='value(status.url)' \
  --project agripulse-prod)

echo $SERVICE_URL
# Output: https://agripulse-backend-xxxxx-uc.a.run.app
```

**Test the endpoints:**

```bash
# Health check
curl ${SERVICE_URL}/health
# Output: {"status":"ok"}

# Create a farm
curl -X POST ${SERVICE_URL}/farm \
  -H "Content-Type: application/json" \
  -d '{
    "district": "Coimbatore",
    "crop": "Tomato",
    "growth_stage": "Flowering"
  }'

# List farms
curl ${SERVICE_URL}/farms

# Get intelligence for a farm (replace with actual farm_id)
curl ${SERVICE_URL}/intelligence/F628C03
```

**If these work, your API is live!** ✅

---

### Step 5.2: Deploy Frontend (Optional)

Currently, the frontend (React) is bundled in the Docker image. The backend serves it.

```bash
# Visit your service URL in a browser
# https://agripulse-backend-xxxxx-uc.a.run.app
```

You should see the AgriPulse React UI.

---

### Step 5.3: Share Your URL

Your live application is at:
```
https://agripulse-backend-xxxxx-uc.a.run.app
```

**Share it with:**
- Team members
- Stakeholders
- Friends
- Anyone with internet!

The URL is **permanent** as long as you keep the service running. To stop paying, you can delete it:

```bash
gcloud run services delete agripulse-backend \
  --region us-central1 \
  --project agripulse-prod
```

---

### Step 5.4: Monitor Your Application

#### View logs:
```bash
# Real-time logs
gcloud run services logs read agripulse-backend \
  --limit 50 \
  --follow \
  --region us-central1 \
  --project agripulse-prod
```

#### View metrics:
1. Go to **Cloud Run** in console
2. Click **agripulse-backend**
3. Click **Metrics** tab
4. See requests, latency, errors

#### Set up alerts (optional):
```bash
# Alert if error rate > 5%
# (Configure in Cloud Console > Monitoring > Alerting)
```

---

## 🔐 Security Best Practices

### Step 6.1: Use Secret Manager for Sensitive Data

Instead of putting API keys in `.env`, use GCP Secret Manager:

```bash
# Store your data.gov.in API key as a secret
echo -n "your-actual-api-key" | \
  gcloud secrets create data-gov-in-key \
  --data-file=- \
  --replication-policy="automatic" \
  --project=agripulse-prod

# Reference it in Cloud Run
gcloud run deploy agripulse-backend \
  --image gcr.io/agripulse-prod/agripulse-backend:latest \
  --set-secrets DATA_GOV_IN_API_KEY=data-gov-in-key:latest \
  # ... other flags
```

**Benefits:**
- Keys never appear in `.env` files
- Automatically rotated
- Audit logging
- Fine-grained access control

---

### Step 6.2: Use Service Accounts Instead of User Credentials

For scheduled jobs (Cloud Scheduler), use a service account:

```bash
# Create a service account
gcloud iam service-accounts create agripulse-scheduler \
  --project=agripulse-prod

# Grant it permissions to run Cloud Run jobs
gcloud projects add-iam-policy-binding agripulse-prod \
  --member=serviceAccount:agripulse-scheduler@agripulse-prod.iam.gserviceaccount.com \
  --role=roles/run.invoker
```

**Benefits:**
- Your credentials never leave your laptop
- Scheduler can only do what you authorize
- Fully auditable

---

### Step 6.3: Enable IAM for Cloud Run

By default, Cloud Run is open to the internet. Restrict it:

```bash
# Remove public access
gcloud run services remove-iam-policy-binding agripulse-backend \
  --member=allUsers \
  --role=roles/run.invoker \
  --region us-central1 \
  --project agripulse-prod

# Only allow specific service accounts
gcloud run services add-iam-policy-binding agripulse-backend \
  --member=serviceAccount:agripulse-scheduler@agripulse-prod.iam.gserviceaccount.com \
  --role=roles/run.invoker \
  --region us-central1 \
  --project agripulse-prod
```

---

## 🚨 Troubleshooting & Common Issues

### Issue 1: "Permission denied" when accessing BigQuery

**Cause:** Service account lacks permissions

**Solution:**
```bash
# Grant Cloud Run service account BigQuery permissions
gcloud projects add-iam-policy-binding agripulse-prod \
  --member=serviceAccount:agripulse-backend@appspot.gserviceaccount.com \
  --role=roles/bigquery.dataEditor
```

---

### Issue 2: "Cloud Run API not enabled"

**Cause:** You forgot to enable the API

**Solution:**
```bash
gcloud services enable run.googleapis.com --project=agripulse-prod
```

---

### Issue 3: "Firestore permission denied"

**Cause:** Service account lacks Firestore permissions

**Solution:**
```bash
gcloud projects add-iam-policy-binding agripulse-prod \
  --member=serviceAccount:agripulse-backend@appspot.gserviceaccount.com \
  --role=roles/datastore.user
```

---

### Issue 4: "Docker build failed"

**Cause:** Dockerfile has errors or missing files

**Solution:**
```bash
# Build locally to see errors
docker build -t agripulse:test .

# Check logs
gcloud builds log --stream=true
```

---

### Issue 5: "AGRIPULSE_MOCK_DATA still using fixtures"

**Cause:** Cloud Run using old environment variables

**Solution:**
```bash
# Redeploy with fresh env vars
gcloud run deploy agripulse-backend \
  --image gcr.io/agripulse-prod/agripulse-backend:latest \
  --set-env-vars "GCP_PROJECT_ID=agripulse-prod,AGRIPULSE_MOCK_DATA=0" \
  --region us-central1 \
  --project agripulse-prod
```

---

## 📊 Cost Optimization

### Understanding GCP Pricing

| Service | Pricing Model | Estimate |
|---------|---------------|----------|
| **Cloud Run** | $0.40/million requests + compute time | $5-20/month |
| **BigQuery** | $6.25 per TB scanned | $5-15/month |
| **Firestore** | $0.06 per 100K reads | $1-5/month |
| **Cloud Storage** | $0.023/GB/month | $0.50/month |
| **Vertex AI** | $0.00 (free for Gemini) | $0 |

**Total estimated cost:** $15-50/month (for small projects)

### Cost-Saving Tips

1. **Use Cloud Run's free tier:**
   - 2 million requests/month free
   - Most small apps stay within this

2. **Query smart in BigQuery:**
   ```sql
   -- Bad (scans entire table)
   SELECT * FROM agripulse_data.weather

   -- Good (scans only required columns)
   SELECT date, district, temperature_c 
   FROM agripulse_data.weather 
   WHERE district = 'Coimbatore'
   ```

3. **Cache frequently-used queries:**
   - Results cached for 24 hours
   - Saves on re-scans

---

## ✅ Complete Checklist: From Zero to Live

### Pre-Deployment
- [ ] GCP account created
- [ ] Project created (`agripulse-prod`)
- [ ] Billing enabled
- [ ] gcloud CLI installed
- [ ] APIs enabled (11 services)
- [ ] Cloud Storage buckets created
- [ ] `.env` file configured locally
- [ ] `gcloud auth application-default login` run

### Database Setup
- [ ] BigQuery dataset & tables created
- [ ] BigQuery views created
- [ ] Synthetic seed data loaded
- [ ] Firestore database created
- [ ] Data ingestion tested (at least weather)

### Containerization
- [ ] Docker image built locally (optional test)
- [ ] Image built on Cloud (Cloud Build)
- [ ] Image pushed to Container Registry

### Deployment
- [ ] Cloud Run service deployed
- [ ] Environment variables set
- [ ] Service is accessible at live URL
- [ ] Health check works (`/health`)
- [ ] Farm creation works (`POST /farm`)
- [ ] Intelligence endpoint works (`GET /intelligence/{farm_id}`)

### Sharing
- [ ] URL copied and shared with team
- [ ] Frontend works at the URL
- [ ] Logs being monitored

---

## 🎓 Key Takeaways (What You've Learned)

1. **Cloud architecture:** Compute (Cloud Run) + Data (BigQuery) + AI (Vertex AI)
2. **IAM & Security:** Service accounts, secrets, permissions
3. **Containerization:** Docker packages your app for the cloud
4. **CI/CD:** Cloud Build automatically builds & deploys on code push
5. **Scalability:** Cloud Run automatically scales from 0 → millions of requests
6. **Cost:** You only pay for what you use (free tier includes plenty)

---

## 🚀 Next Steps (What to Do Now)

1. **Automate deployments:**
   - Every time you push to GitHub, Cloud Build automatically redeploys
   - Setup `.github/workflows` (configured in the project)

2. **Schedule daily ingestion:**
   - Cloud Scheduler triggers data refresh daily
   - Check `infra/deploy.sh` for scheduler setup

3. **Custom domain:**
   - Map `agripulse.example.com` to your Cloud Run URL
   - (Requires domain ownership)

4. **Analytics dashboard:**
   - Use Looker Studio to visualize BigQuery data
   - Create dashboards for stakeholders

5. **Mobile app:**
   - Build a mobile frontend using the same API
   - Your backend serves both web + mobile

---

## 📚 Additional Resources

| Topic | Link |
|-------|------|
| Cloud Run Docs | [cloud.google.com/run/docs](https://cloud.google.com/run/docs) |
| BigQuery Docs | [cloud.google.com/bigquery/docs](https://cloud.google.com/bigquery/docs) |
| Firestore Docs | [cloud.google.com/firestore/docs](https://cloud.google.com/firestore/docs) |
| Vertex AI Docs | [cloud.google.com/vertex-ai/docs](https://cloud.google.com/vertex-ai/docs) |
| gcloud CLI Reference | [cloud.google.com/sdk/gcloud](https://cloud.google.com/sdk/gcloud) |
| GCP Pricing | [cloud.google.com/pricing](https://cloud.google.com/pricing) |

---

## 💬 Questions? 

If you get stuck:
1. Check the **Troubleshooting** section above
2. Look at **Cloud Logging** for error messages: `gcloud run services logs read agripulse-backend --limit 100`
3. Check **Cloud Console** for API errors
4. Review `.env` file for misconfigurations

Good luck! 🎉

---

**Created by:** Professor CloudAI  
**Last Updated:** 2026-09-03  
**For:** AgriPulse Agricultural Decision System
