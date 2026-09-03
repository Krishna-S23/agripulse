# 🗺️ The AgriPulse GCP Deployment Journey Map

## Your Path from Zero to Live URL

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     YOU START HERE (With a Laptop)                      │
└────────────────────────────────────────┬────────────────────────────────┘
                                         │
                    ▼
        ╔════════════════════════════════════════════╗
        ║    PHASE 1: SETUP (20 minutes)            ║
        ║  ✅ Create GCP Project                    ║
        ║  ✅ Install gcloud CLI                    ║
        ║  ✅ Enable 11 APIs                        ║
        ║  ✅ Create 2 Cloud Storage Buckets        ║
        ║  ✅ Configure .env                        ║
        ║  ✅ Authenticate locally                  ║
        ╚═════════════┬═════════════════════════════╝
                      │
                    ▼
        ╔════════════════════════════════════════════╗
        ║    PHASE 2: DATABASE (15 minutes)         ║
        ║  ✅ Create BigQuery Dataset               ║
        ║  ✅ Create Tables & Views                 ║
        ║  ✅ Load Synthetic Test Data              ║
        ║  ✅ Create Firestore Database             ║
        ║  ✅ Ingest Real Weather Data (optional)   ║
        ╚═════════════┬═════════════════════════════╝
                      │
                    ▼
        ╔════════════════════════════════════════════╗
        ║    PHASE 3: CONTAINERIZE (5 minutes)      ║
        ║  ✅ Build Docker Image on Cloud Build     ║
        ║  ✅ Push to Container Registry            ║
        ║  ✅ Image ready for Cloud Run             ║
        ╚═════════════┬═════════════════════════════╝
                      │
                    ▼
        ╔════════════════════════════════════════════╗
        ║    PHASE 4: DEPLOY (3 minutes)            ║
        ║  ✅ Deploy to Cloud Run                   ║
        ║  ✅ Set Environment Variables             ║
        ║  ✅ Enable Public Access                  ║
        ║  ✅ Service is LIVE                       ║
        ╚═════════════┬═════════════════════════════╝
                      │
                    ▼
        ╔════════════════════════════════════════════╗
        ║    PHASE 5: VERIFY & SHARE (2 minutes)   ║
        ║  ✅ Test Health Endpoint                  ║
        ║  ✅ Create a Farm                         ║
        ║  ✅ Get Intelligence Report               ║
        ║  ✅ Copy Shareable URL                    ║
        ║  ✅ Send to Friends/Team                  ║
        ╚═════════════┬═════════════════════════════╝
                      │
                    ▼
    ╔═══════════════════════════════════════════════════╗
    │   🎉 SUCCESS! Your app is live at:              │
    │   https://agripulse-backend-xxxxx.a.run.app    │
    ╚═══════════════════════════════════════════════════╝

Total Time: ~45 minutes ⏱️
```

---

## 🎯 What Happens at Each Phase

### PHASE 1: SETUP - You build your foundation

**What you're doing:**
- Creating a GCP "office building" (Project)
- Installing the key to the office (gcloud CLI)
- Turning on electricity (APIs)
- Building storage rooms (Cloud Storage buckets)

**Why it matters:**
- Without these, you have nowhere to deploy
- Like preparing construction site before building

**Key Resource: gcloud**
```bash
# Your command-line power tool
gcloud projects create agripulse-prod
gcloud services enable run.googleapis.com bigquery.googleapis.com ...
gsutil mb gs://agripulse-raw-agripulse-prod
```

---

### PHASE 2: DATABASE - You prepare the data layer

**What you're doing:**
- Building a data warehouse (BigQuery)
- Setting up document storage (Firestore)
- Filling it with test data
- Creating shortcuts (views) for common queries

**Why it matters:**
- Your app needs somewhere to read/write data
- Structured, fast, scalable data storage

**Visual:**
```
┌────────────────────────────────────────┐
│        BigQuery Dataset                │
│   (agripulse_data)                    │
├────────────────────────────────────────┤
│ Tables:                                │
│  • farm (45 farms)                     │
│  • weather (1000s of readings)         │
│  • soil_conditions (synthetic)         │
│  • market_prices (daily updates)       │
│  • crop_history (annual data)          │
│                                        │
│ Views (shortcuts):                     │
│  • v_rainfall_7day                     │
│  • v_latest_soil                       │
│  • v_weekly_price_trend                │
└────────────────────────────────────────┘
         ▲
         │ Query
         │
      Your App (Cloud Run)
```

---

### PHASE 3: CONTAINERIZE - You package your app

**What you're doing:**
- Taking your code + dependencies
- Wrapping in a Docker container
- Building on GCP's infrastructure
- Storing in Container Registry

**Why it matters:**
- Your code needs to run the same everywhere
- Docker = guaranteed consistency
- Container Registry = version control for Docker images

**Visual:**
```
Your Code
    ↓
[Dockerfile] ← Tells Docker how to build
    ↓
Build on Cloud Build
    ↓
Docker Image (agripulse-backend:latest)
    ↓
Container Registry (gcr.io/agripulse-prod/)
    ↓
Ready for Cloud Run
```

---

### PHASE 4: DEPLOY - Your app goes live

**What you're doing:**
- Telling Cloud Run "use this Docker image"
- Setting environment variables
- Making service public
- GCP automatically starts containers

**Why it matters:**
- Cloud Run handles:
  - 0 users? → 0 running containers (costs $0)
  - 1000 users? → Auto-scales up
  - Done? → Scale back down

**Visual:**
```
1 request arrives
    ↓
Cloud Run says: "Need a container"
    ↓
Container spins up (1-2 seconds)
    ↓
Your app processes request
    ↓
Returns response
    ↓
Response sent to user
    ↓
10 minutes no traffic?
    ↓
Container shuts down (costs $0)
```

---

### PHASE 5: VERIFY & SHARE - You test & celebrate

**What you're doing:**
- Testing API endpoints
- Creating sample data
- Getting your public URL
- Sharing with team/friends

**Your Shareable URL looks like:**
```
https://agripulse-backend-a1b2c3d4-uc.a.run.app
```

Anyone with this URL can access your app! 🌍

---

## 📊 The Three Layers You're Building

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: FRONTEND (Optional via Cloud Run)             │
│  • React web app                                        │
│  • Served at your Cloud Run URL                         │
│  • Same server as backend                              │
└──────────────────┬──────────────────────────────────────┘
                   │ (Makes API calls)
                   ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: BACKEND (Cloud Run)                          │
│  • FastAPI server (your Python app)                    │
│  • Stateless (no data stored locally)                  │
│  • Scales automatically                                │
│  • Publicly accessible via HTTPS                       │
└──────────────────┬──────────────────────────────────────┘
                   │ (Queries/Writes)
        ┌──────────┼──────────┐
        ▼          ▼          ▼
┌──────────────┐ ┌────────┐ ┌─────────────┐
│  BigQuery    │ │Firestore│ │ Vertex AI   │
│  (Analytics) │ │(Storage) │ │ (AI/ML)    │
└──────────────┘ └────────┘ └─────────────┘
  Layer 3: Data
```

**Key Principle:** Each layer can be changed independently
- Update code → redeploy → instant update
- Add more database → no app change needed
- Switch to different AI model → update env var only

---

## 🔄 The Daily Workflow (After Deployment)

```
Day 1: You deploy
  └─→ Everyone gets a URL
      └─→ They start using your app ✅

Day 2: You found a bug
  └─→ Fix code locally
      └─→ Push to GitHub
          └─→ Cloud Build auto-builds
              └─→ Cloud Run auto-deploys
                  └─→ Users see fix (5 minutes) ✅

Day 3: You want more data
  └─→ Ingestion job runs automatically daily
      └─→ BigQuery updated
          └─→ App shows new data (no code change) ✅

Day 4: You want to scale down costs
  └─→ Adjust Cloud Run CPU/Memory
      └─→ Change costs immediately ✅
```

---

## 💰 The Cost Structure

```
┌─────────────────────────────────────────────────────────┐
│              Your Monthly Costs                         │
├─────────────────────────────────────────────────────────┤
│ Cloud Run:              $5-20    (first 2M requests free)
│ BigQuery:              $5-15    (1TB scan free)
│ Firestore:             $1-5     (lightweight)
│ Cloud Storage:         $0.50    (minimal)
│ Vertex AI:             $0       (Gemini free for Cloud)
├─────────────────────────────────────────────────────────┤
│ TOTAL:                 $12-40   (typical small app)     │
│ Free tier limit:       $300     (first 90 days)        │
└─────────────────────────────────────────────────────────┘

You pay ONLY for what you use:
  • No servers idling
  • No reserved capacity
  • Scales cost with traffic
```

---

## 🚨 Critical Checkpoints

### Before You Deploy, Verify:

```
CHECKPOINT 1: Can you connect locally?
└─→ gcloud auth application-default login ✅
└─→ gcloud bq ls ✅
└─→ Can query BigQuery from laptop ✅

CHECKPOINT 2: Is Docker image built?
└─→ gcr.io/agripulse-prod/agripulse-backend:latest exists ✅
└─→ gcloud container images list shows your image ✅

CHECKPOINT 3: Is Cloud Run accessible?
└─→ gcloud run services describe agripulse-backend ✅
└─→ Can curl your service URL ✅
└─→ /health returns {"status":"ok"} ✅

CHECKPOINT 4: Does data flow work?
└─→ Create farm: POST /farm ✅
└─→ Data saved to Firestore ✅
└─→ Query intelligence: GET /intelligence/{farm_id} ✅
└─→ Data comes from BigQuery ✅

CHECKPOINT 5: Is it shareable?
└─→ Give URL to friend ✅
└─→ Friend can access from their phone ✅
└─→ App works without errors ✅
```

---

## 📈 What Happens When You Get Users

```
Scenario: Your app goes viral (50K requests/day)

Day 1:
  • Cloud Run receives 50,000 requests
  • Auto-scales from 1 → 100 containers
  • All requests handled
  • Cost increases proportionally

Day 2-7:
  • Load stays high
  • Cloud Run maintains 100 containers
  • You pay for them

Day 8+:
  • Traffic drops
  • Cloud Run scales back down
  • Costs drop automatically

Result: You never paid for infrastructure you didn't use ✅
```

---

## 🔐 Security Checkpoints

After deployment, secure your app:

```
MUST DO:
✅ Store API keys in Secret Manager (not .env)
✅ Use service accounts (not user credentials)
✅ Enable Cloud Audit Logging
✅ Review IAM permissions (least privilege)

GOOD TO DO:
✅ Set up monitoring/alerts
✅ Use custom domain (optional)
✅ Enable CORS only for your domain
✅ Regular backups of BigQuery data

OPTIONAL:
⭕ Use VPC for private networks
⭕ Set up DDoS protection
⭕ Enable encryption at rest
```

---

## 📞 You Get Stuck? Common Scenarios

### "My app isn't accessible"
```
Probable cause: Cloud Run service not deployed
Step 1: gcloud run services list --region=us-central1
Step 2: Is agripulse-backend there?
Step 3: If not: gcloud run deploy agripulse-backend ...
Step 4: Retry
```

### "I get permission errors"
```
Probable cause: Service account needs more permissions
Step 1: gcloud projects get-iam-policy agripulse-prod
Step 2: Find agripulse-backend@appspot.gserviceaccount.com
Step 3: Grant missing role
Step 4: Redeploy
```

### "BigQuery shows no data"
```
Probable cause: Ingestion didn't run
Step 1: cd ingestion && python weather_ingest.py
Step 2: Verify file in Cloud Storage: gsutil ls gs://agripulse-processed-...
Step 3: Check BigQuery: bq query "SELECT COUNT(*) FROM agripulse_data.weather"
Step 4: If 0 rows: check API keys, network
```

### "Can't build Docker image"
```
Probable cause: Dockerfile error or missing files
Step 1: gcloud builds log --stream=true
Step 2: Look for error in output
Step 3: Fix code or Dockerfile
Step 4: gcloud builds submit again
```

---

## 🎓 What You'll Learn

By completing this journey, you'll understand:

1. **Cloud Architecture**
   - Compute (Cloud Run)
   - Data (BigQuery + Firestore)
   - AI (Vertex AI)

2. **DevOps**
   - Docker containerization
   - CI/CD (Cloud Build)
   - Infrastructure as Code

3. **GCP Fundamentals**
   - Projects, APIs, IAM
   - Service accounts, authentication
   - Scaling, monitoring, logging

4. **Best Practices**
   - Secrets management
   - Security hardening
   - Cost optimization

---

## 🏆 Success Criteria

You're done when:

- ✅ You have a Cloud Run URL
- ✅ URL is accessible from anywhere (phone, laptop, friend's device)
- ✅ You can create a farm via the API
- ✅ Farm data is saved in Firestore
- ✅ You can get intelligence report (queries BigQuery)
- ✅ No hardcoded secrets in .env
- ✅ You can share the URL and it works

---

## 🚀 The Very Next Step

**Right now:**
1. Open `GCP_DEPLOYMENT_PROFESSOR_GUIDE.md` (the full guide)
2. Open `GCP_QUICK_REFERENCE.md` (copy-paste commands)
3. Start with Phase 1 (Project Setup - 20 minutes)
4. Follow along step-by-step

**In 45 minutes:**
You'll have a live, shareable app URL 🎉

---

**Created by:** Your Professor CloudAI  
**Status:** Ready to Go! 🚀
