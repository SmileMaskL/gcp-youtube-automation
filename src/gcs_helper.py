# src/gcs_helper.py

import logging
from google.cloud import storage

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def upload_to_gcs(bucket_name, source_file, dest_blob, project_id):
    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(dest_blob)
    blob.upload_from_filename(source_file)
    logger.info(f"✅ Uploaded '{source_file}' to 'gs://{bucket_name}/{dest_blob}'")

def download_from_gcs(bucket_name, blob_name, dest_file, project_id):
    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(dest_file)
    logger.info(f"✅ Downloaded 'gs://{bucket_name}/{blob_name}' to '{dest_file}'")

def delete_from_gcs(bucket_name, blob_name, project_id):
    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()
    logger.info(f"✅ Deleted 'gs://{bucket_name}/{blob_name}'")
