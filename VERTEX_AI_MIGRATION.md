# Gemini API → Vertex AI Migration Guide

## Overview
AgriPulse has been migrated from **Gemini API** (API-key based) to **Vertex AI** (GCP-native authentication). This makes the application deployment-ready for Google Cloud Platform with automatic credential handling.

---

## Changes Made

### 1. **Dependencies** (`requirements.txt`)
```diff
- google-generativeai>=0.8.0
+ google-cloud-aiplatform>=1.42.0
```

**Why**: Vertex AI uses the `google-cloud-aiplatform` SDK for GCP-native integration.

---

### 2. **Configuration** (`.env.example`)

**Removed**:
```
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.6-flash
```

**Added**:
```
GCP_REGION=us-central1
VERTEX_AI_MODEL=gemini-2.0-flash
```

**Why**: 
- Vertex AI uses **Application Default Credentials (ADC)** — no API key needed
- GCP_PROJECT_ID + GCP_REGION are required for authentication
- No hardcoded secrets in environment variables

---

### 3. **Orchestrator** (`agents/orchestrator.py`)

#### Environment Variables
```python
# OLD
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

# NEW
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
GCP_REGION = os.environ.get("GCP_REGION", "us-central1")
VERTEX_AI_MODEL = os.environ.get("VERTEX_AI_MODEL", "gemini-2.0-flash")
```

#### Model Initialization
```python
# OLD
import google.generativeai as genai
genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name)

# NEW
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project=project_id, location=region)
model = GenerativeModel(model_name)
```

#### Function Renaming
- `_call_gemini()` → `_call_vertex_ai()`
- `_call_gemini()` kept as deprecated wrapper for backwards compatibility
- Updated all calls: `_explain()` and `answer_question()` now call `_call_vertex_ai()`

#### Error Handling
```python
# OLD: Checked for API key
if not api_key:
    return _fallback_explanation(prompt)

# NEW: Checks for project ID
if not project_id:
    logger.warning("GCP_PROJECT_ID not set, falling back to template explanation")
    return _fallback_explanation(prompt)
```

---

### 4. **Backend** (`backend/main.py`)
Updated docstring comment from "Gemini" to "Vertex AI"

---

## Deployment Instructions

### **Local Development**

1. **Set Environment Variables**
   ```bash
   export GCP_PROJECT_ID=your-gcp-project-id
   export GCP_REGION=us-central1
   export VERTEX_AI_MODEL=gemini-2.0-flash
   export AGRIPULSE_MOCK_DATA=1  # For local testing without GCP
   ```

2. **Authenticate with Google Cloud**
   ```bash
   gcloud auth application-default login
   ```
   This sets up Application Default Credentials for local development.

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   cd backend
   uvicorn main:app --reload --port 8080
   ```

---

### **Google Cloud Run Deployment**

1. **Create Cloud Run Service**
   ```bash
   gcloud run deploy agripulse-backend \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

2. **Set Environment Variables in Cloud Run**
   ```bash
   gcloud run services update agripulse-backend \
     --set-env-vars "GCP_PROJECT_ID=your-project-id,GCP_REGION=us-central1,VERTEX_AI_MODEL=gemini-2.0-flash,AGRIPULSE_MOCK_DATA=0"
   ```

3. **Service Account Permissions**
   Ensure the Cloud Run service account has:
   - `roles/aiplatform.user` (Vertex AI API access)
   - `roles/bigquery.dataEditor` (BigQuery access)
   - `roles/datastore.user` (Firestore access)
   - `roles/storage.objectViewer` (Cloud Storage access)

   ```bash
   gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
     --member=serviceAccount:cloud-run-sa@YOUR-PROJECT-ID.iam.gserviceaccount.com \
     --role=roles/aiplatform.user
   ```

---

### **Dockerfile Updates** (if needed)

The existing Dockerfile should work as-is. Ensure it installs the updated `requirements.txt`:

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

---

## Available Models

Vertex AI supports multiple generative models. Update `VERTEX_AI_MODEL` as needed:

| Model | Best For | Cost | Latency |
|-------|----------|------|---------|
| `gemini-2.0-flash` | Fast inference, agriculture explanations | Low | Low |
| `gemini-1.5-pro` | Complex reasoning, long context | Higher | Medium |
| `gemini-1.5-flash` | Balanced performance | Medium | Low |

---

## Authentication Methods

### **Application Default Credentials (ADC)** ✅ Recommended
```python
vertexai.init(project=project_id, location=region)
# Automatically uses credentials from:
# 1. GOOGLE_APPLICATION_CREDENTIALS env var (service account JSON)
# 2. gcloud login credentials (local development)
# 3. Cloud Run / Compute Engine service account (GCP-hosted)
```

### **Service Account JSON** (explicit)
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
# Then use ADC as above
```

---

## Fallback Behavior

If GCP credentials are unavailable:
1. `_call_vertex_ai()` logs a warning
2. Falls back to template-based explanation
3. Application continues to function (non-critical failure)

Example fallback output:
```
[Template explanation — set GCP_PROJECT_ID and GCP_REGION for full natural-language output] 
Based on current evidence, please review the flagged data points for this recommendation.
```

---

## Testing

### **Local Mock Mode**
```bash
export AGRIPULSE_MOCK_DATA=1
export GCP_PROJECT_ID=test-project  # Still required for initialization
python agents/orchestrator.py
```

### **With Real GCP**
```bash
export AGRIPULSE_MOCK_DATA=0
export GCP_PROJECT_ID=your-actual-project
export GCP_REGION=us-central1
python agents/orchestrator.py
```

---

## Migration Checklist

- [x] Update `requirements.txt` (google-cloud-aiplatform)
- [x] Update `.env.example` (GCP_REGION, VERTEX_AI_MODEL)
- [x] Replace Gemini calls with Vertex AI in `orchestrator.py`
- [x] Update environment variable handling
- [x] Update fallback explanation message
- [x] Update backend docstring
- [ ] Test locally with mock data
- [ ] Test with real GCP credentials
- [ ] Deploy to Cloud Run
- [ ] Monitor Vertex AI API quotas and costs

---

## Benefits of Vertex AI

✅ **GCP-Native Integration**: Works seamlessly with BigQuery, Firestore, Cloud Storage  
✅ **No API Keys**: Uses IAM service accounts for secure authentication  
✅ **Multi-Region Support**: Deploy close to your data  
✅ **Cost Optimization**: Integrated billing with GCP  
✅ **Model Selection**: Easy to switch between Gemini models  
✅ **Audit Logging**: All API calls logged in Cloud Audit Logs  

---

## Troubleshooting

### **Error: "PERMISSION_DENIED: Cloud Generative AI API has not been enabled"**
```bash
gcloud services enable aiplatform.googleapis.com --project=YOUR-PROJECT-ID
```

### **Error: "ADC not available"**
```bash
# Local development
gcloud auth application-default login

# Cloud Run: Ensure service account has aiplatform.user role
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member=serviceAccount:YOUR-SERVICE-ACCOUNT@iam.gserviceaccount.com \
  --role=roles/aiplatform.user
```

### **Error: "Model not found: gemini-2.0-flash"**
Check available models in your region:
```bash
gcloud ai models list --location=us-central1
```

---

## Rollback to Gemini (if needed)

To revert to Gemini API:
1. Restore old `requirements.txt` with `google-generativeai`
2. Restore `GEMINI_API_KEY` and `GEMINI_MODEL` in `.env`
3. Replace `_call_vertex_ai` with original `_call_gemini` implementation

---

## References

- [Vertex AI Generative Models](https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform.generative_models)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)
- [Cloud Run Deployment Guide](https://cloud.google.com/run/docs/quickstarts/build-and-deploy)
- [Vertex AI Quotas and Limits](https://cloud.google.com/vertex-ai/quotas)
