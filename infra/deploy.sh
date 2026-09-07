#!/usr/bin/env bash
# AgriPulse deployment script.
# Usage: PROJECT_ID=your-project ./deploy.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID env var}"
REGION="${REGION:-asia-south1}"
SERVICE_NAME="agripulse-backend"

echo "== Enabling required APIs =="
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com \
  firestore.googleapis.com \
  aiplatform.googleapis.com \
  cloudscheduler.googleapis.com \
  --project "$PROJECT_ID"

echo "== Creating BigQuery dataset + tables =="
bq query --project_id="$PROJECT_ID" --location=asia-south1 --use_legacy_sql=false < bigquery_schema.sql

echo "== Building and deploying to Cloud Run =="
gcloud builds submit --tag "gcr.io/${PROJECT_ID}/${SERVICE_NAME}" --project "$PROJECT_ID" ..

gcloud run deploy "$SERVICE_NAME" \
  --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}" \
  --platform managed \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},VERTEX_AI_MODEL=${VERTEX_AI_MODEL:-gemini-2.0-flash},BQ_DATASET=agripulse_data,AGRIPULSE_MOCK_DATA=0" \
  --set-secrets "DATA_GOV_IN_API_KEY=data-gov-in-key:latest"

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" --project "$PROJECT_ID" --format='value(status.url)')
echo "Deployed: ${SERVICE_URL}"

echo "== Scheduling daily ingestion (Cloud Scheduler -> Cloud Run Jobs) =="
# Assumes ingestion is also containerized as a Cloud Run Job named agripulse-ingest.
# Build/deploy that job separately (see infra/deploy_ingest_job.sh), then:
gcloud scheduler jobs create http agripulse-daily-ingest \
  --project "$PROJECT_ID" \
  --location "$REGION" \
  --schedule "0 5 * * *" \
  --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/agripulse-ingest:run" \
  --http-method POST \
  --oauth-service-account-email "agripulse-scheduler@${PROJECT_ID}.iam.gserviceaccount.com" \
  || echo "Scheduler job already exists or ingest job not yet deployed — see README."

echo "Done."
