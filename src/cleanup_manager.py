import os
import shutil
import logging
from google.cloud import storage # ⚠️ 추가: Cloud Storage 사용을 위해 임포트

logger = logging.getLogger(__name__)

def clean_up_old_files():
    """
    생성된 비디오, 오디오, 이미지 파일 등 불필요한 임시 파일들을 삭제합니다.
    Cloud Storage 사용 시, 해당 버킷의 파일을 삭제하는 로직도 포함되어야 합니다.
    """
    logger.info("임시 파일 및 폴더 정리 시작...")

    # 1. 로컬 임시 폴더 정리
    folders_to_clean = ['output', 'tmp', 'audio_files', 'video_clips', 'thumbnails']
    for folder in folders_to_clean:
        full_path = os.path.join(os.getcwd(), folder) # 현재 작업 디렉토리 기준
        if os.path.exists(full_path):
            try:
                shutil.rmtree(full_path)
                logger.info(f"로컬 폴더 '{folder}'를 성공적으로 정리했습니다.")
            except OSError as e:
                logger.error(f"로컬 폴더 '{folder}' 정리 중 오류 발생: {e}")
        # 폴더가 없으면 다시 생성 (gitkeep 파일 제거 방지)
        os.makedirs(full_path, exist_ok=True)
        with open(os.path.join(full_path, '.gitkeep'), 'w') as f:
            pass # .gitkeep 파일 유지

    # 2. Cloud Storage 버킷 정리
    try:
        bucket_name = os.environ.get("GCP_BUCKET_NAME")
        if bucket_name:
            client = storage.Client()
            bucket = client.bucket(bucket_name) # bucket() 메서드로 변경
            
            # 특정 접두사를 가진 임시 파일들만 삭제 (예: 'temp_uploads/')
            # 프로젝트에서 임시 파일을 저장하는 경로에 맞춰 접두사를 설정하세요.
            blobs = bucket.list_blobs(prefix="temp_uploads/") 
            
            deleted_count = 0
            for blob in blobs:
                blob.delete()
                logger.info(f"Cloud Storage에서 파일 '{blob.name}' 삭제.")
                deleted_count += 1
            logger.info(f"Cloud Storage에서 총 {deleted_count}개의 임시 파일을 정리했습니다.")
        else:
            logger.warning("GCP_BUCKET_NAME 환경 변수가 설정되지 않아 Cloud Storage를 정리할 수 없습니다.")
    except Exception as e:
        logger.error(f"Cloud Storage 정리 중 오류 발생: {e}", exc_info=True)
