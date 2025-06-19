# src/utils.py
import os
import uuid
import logging
from google.cloud import storage

logger = logging.getLogger(__name__)

def generate_unique_id():
    """고유한 ID를 생성합니다."""
    return str(uuid.uuid4())[:8]

def upload_to_gcs(bucket_name: str, source_file_name: str, destination_blob_name: str):
    """
    로컬 파일을 Google Cloud Storage에 업로드합니다.

    Args:
        bucket_name (str): 대상 버킷의 이름.
        source_file_name (str): 업로드할 로컬 파일의 경로.
        destination_blob_name (str): GCS에 저장될 파일의 경로 및 이름.
    """
    if not os.path.exists(source_file_name):
        logger.error(f"Source file not found for GCS upload: {source_file_name}")
        return False
        
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        logger.info(f"File {source_file_name} uploaded to gs://{bucket_name}/{destination_blob_name}.")
        return True
    except Exception as e:
        logger.error(f"Error uploading {source_file_name} to GCS: {e}", exc_info=True)
        return False

def download_from_gcs(bucket_name: str, source_blob_name: str, destination_file_name: str):
    """
    Google Cloud Storage에서 파일을 로컬로 다운로드합니다.

    Args:
        bucket_name (str): 소스 버킷의 이름.
        source_blob_name (str): GCS에 있는 파일의 경로 및 이름.
        destination_file_name (str): 다운로드하여 저장할 로컬 파일의 경로.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        
        # 대상 디렉토리 생성
        os.makedirs(os.path.dirname(destination_file_name), exist_ok=True)
        
        blob.download_to_filename(destination_file_name)
        logger.info(f"File gs://{bucket_name}/{source_blob_name} downloaded to {destination_file_name}.")
        return True
    except Exception as e:
        logger.error(f"Error downloading {source_blob_name} from GCS: {e}", exc_info=True)
        return False

def check_gcs_file_exists(bucket_name: str, blob_name: str):
    """
    Google Cloud Storage에 파일이 존재하는지 확인합니다.

    Args:
        bucket_name (str): 버킷 이름.
        blob_name (str): 파일의 경로 및 이름.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.exists()
    except Exception as e:
        logger.error(f"Error checking GCS file existence for {blob_name}: {e}", exc_info=True)
        return False

def delete_gcs_file(bucket_name: str, blob_name: str):
    """
    Google Cloud Storage에서 파일을 삭제합니다.

    Args:
        bucket_name (str): 버킷 이름.
        blob_name (str): 삭제할 파일의 경로 및 이름.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()
        logger.info(f"File gs://{bucket_name}/{blob_name} deleted.")
        return True
    except Exception as e:
        logger.error(f"Error deleting GCS file {blob_name}: {e}", exc_info=True)
        return False

# 기존 utils.py의 다른 함수들은 여기에 통합되거나 필요에 따라 재구성
# 예:
def ensure_dir(directory: str):
    """지정된 디렉토리가 없으면 생성합니다."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    from src.config import setup_logging
    setup_logging()

    # GCP 환경 변수 설정 (로컬 테스트용)
    test_bucket_name = os.environ.get("GCP_BUCKET_NAME")
    test_project_id = os.environ.get("GCP_PROJECT_ID")

    if not test_bucket_name or not test_project_id:
        print("Please set GCP_BUCKET_NAME and GCP_PROJECT_ID environment variables for local testing.")
    else:
        print(f"Testing GCS operations with bucket: {test_bucket_name}")
        
        # 테스트 파일 생성
        test_file_content = "This is a test file for GCS upload."
        test_local_path = "test_upload.txt"
        test_gcs_path = "test_uploads/test_upload.txt"
        
        with open(test_local_path, "w") as f:
            f.write(test_file_content)
        
        print(f"\n--- Uploading {test_local_path} to GCS ---")
        if upload_to_gcs(test_bucket_name, test_local_path, test_gcs_path):
            print("Upload successful!")
        else:
            print("Upload failed.")

        print(f"\n--- Checking if {test_gcs_path} exists in GCS ---")
        if check_gcs_file_exists(test_bucket_name, test_gcs_path):
            print("File exists!")
        else:
            print("File does not exist.")

        test_download_path = "downloaded_test_file.txt"
        print(f"\n--- Downloading {test_gcs_path} from GCS to {test_download_path} ---")
        if download_from_gcs(test_bucket_name, test_gcs_path, test_download_path):
            print("Download successful!")
            with open(test_download_path, "r") as f:
                print(f"Downloaded content: {f.read()}")
            os.remove(test_download_path) # 다운로드된 파일 삭제
        else:
            print("Download failed.")

        print(f"\n--- Deleting {test_gcs_path} from GCS ---")
        if delete_gcs_file(test_bucket_name, test_gcs_path):
            print("Deletion successful!")
        else:
            print("Deletion failed.")

        os.remove(test_local_path) # 업로드 테스트 파일 삭제
