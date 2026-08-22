"""
Shared GCP client helpers for ingestion scripts.

Requires: pip install google-cloud-bigquery google-cloud-storage
Auth: run `gcloud auth application-default login` locally, or rely on the
default service account when running inside Cloud Run / Cloud Run Jobs.
"""
import os
import logging
from dotenv import load_dotenv, find_dotenv

# Loads the .env file at the project root, regardless of which directory this
# script is actually run from (find_dotenv walks up parent directories).
load_dotenv(find_dotenv(usecwd=True))

from google.cloud import bigquery
from google.cloud import storage

logger = logging.getLogger("agripulse.ingestion")
logging.basicConfig(level=logging.INFO)

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "your-gcp-project-id")
DATASET = os.environ.get("BQ_DATASET", "agripulse_data")
RAW_BUCKET = os.environ.get("RAW_BUCKET", "agripulse-raw")
PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET", "agripulse-processed")


def get_bq_client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT_ID)


def get_storage_client() -> storage.Client:
    return storage.Client(project=PROJECT_ID)


def upload_to_gcs(local_path: str, bucket_name: str, blob_name: str) -> str:
    """Uploads a local file to GCS and returns the gs:// URI."""
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    uri = f"gs://{bucket_name}/{blob_name}"
    logger.info("Uploaded %s -> %s", local_path, uri)
    return uri


def load_csv_to_bq(gcs_uri: str, table_name: str, write_disposition: str = "WRITE_APPEND"):
    """Loads a CSV from GCS into a BigQuery table, autodetecting schema
    on first load. For production, replace autodetect with an explicit
    schema matching bigquery_schema.sql."""
    client = get_bq_client()
    table_ref = f"{PROJECT_ID}.{DATASET}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=write_disposition,
    )
    load_job = client.load_table_from_uri(gcs_uri, table_ref, job_config=job_config)
    load_job.result()  # blocks until finished
    logger.info("Loaded %s rows into %s", load_job.output_rows, table_ref)
    return load_job.output_rows
