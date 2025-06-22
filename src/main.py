# main.py
import functions_framework
import os
import logging
from youtube_uploader import upload_video # youtube_uploader.py에서 함수 임포트
# (선택 사항) GCS에서 파일 다운로드용 라이브러리
from google.cloud import storage

logging.basicConfig(level=logging.INFO)

@functions_framework.http
def trigger_youtube_upload(request):
    logging.info("Cloud Function 'trigger_youtube_upload' started.")

    # 🚨 중요: 여기에 실제 영상 생성 로직을 추가해야 합니다.
    # 예시: GCS(Google Cloud Storage)에서 미리 준비된 영상 파일을 다운로드하여 사용
    # 또는 Cloud Function 내부에서 moviepy 같은 라이브러리로 영상 생성

    # 1. 영상 파일 경로 설정 (Cloud Function은 /tmp에만 쓰기 가능)
    video_filename = "my_awesome_short.mp4" # 원하는 파일명
    video_file_path = f"/tmp/{video_filename}"

    # 2. 영상 생성 또는 다운로드 로직 (선택 1: GCS에서 다운로드)
    gcs_bucket_name = os.environ.get("GCS_BUCKET_NAME") # GitHub Actions에서 환경변수로 전달
    gcs_video_path = os.environ.get("GCS_VIDEO_PATH") # GitHub Actions에서 환경변수로 전달 (예: "raw_videos/my_video.mp4")

    if gcs_bucket_name and gcs_video_path:
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(gcs_bucket_name)
            blob = bucket.blob(gcs_video_path)
            blob.download_to_filename(video_file_path)
            logging.info(f"Video downloaded from GCS: gs://{gcs_bucket_name}/{gcs_video_path} to {video_file_path}")
        except Exception as e:
            logging.error(f"Failed to download video from GCS: {e}")
            return "Failed to download video", 500
    else:
        # 🚨 중요: GCS를 사용하지 않는다면 여기에 "영상 생성 로직"을 직접 구현해야 합니다.
        # 예시: 더미 파일 생성 (실제 사용 아님)
        try:
            with open(video_file_path, "wb") as f:
                f.write(b"This is a dummy video file for testing. Replace with real video content!")
            logging.warning(f"No GCS path provided. Created a dummy video file at {video_file_path}. Please replace with actual video generation.")
        except Exception as e:
            logging.error(f"Error creating dummy video file: {e}")
            return "Error creating dummy video file", 500
        # 예시: moviepy를 사용하여 간단한 영상 생성 (추가 라이브러리 필요)
        # from moviepy.editor import ColorClip, concatenate_videoclips
        # clip1 = ColorClip((640, 480), color=(255,0,0), duration=5) # 5초 빨간색 영상
        # final_clip = concatenate_videoclips([clip1])
        # final_clip.write_videofile(video_file_path, fps=24, codec="libx264")
        # logging.info(f"Generated a simple video at {video_file_path}")


    # 환경 변수에서 영상 메타데이터 가져오기 (GitHub Actions에서 전달)
    video_title = os.environ.get("VIDEO_TITLE", "자동화 유튜브 쇼츠")
    video_description = os.environ.get("VIDEO_DESCRIPTION", "이 영상은 자동화된 스크립트로 업로드되었습니다.")
    # 태그는 콤마로 구분된 문자열을 리스트로 변환
    video_tags = [tag.strip() for tag in os.environ.get("VIDEO_TAGS", "shorts,자동화,유튜브").split(',') if tag.strip()]
    video_category_id = os.environ.get("VIDEO_CATEGORY_ID", "22") # People & Blogs
    video_privacy_status = os.environ.get("VIDEO_PRIVACY_STATUS", "private") # 'public', 'private', 'unlisted'

    try:
        response = upload_video(
            video_file_path,
            video_title,
            video_description,
            video_tags,
            video_category_id,
            video_privacy_status
        )
        logging.info("Video upload process completed successfully.")

        # 업로드 완료 후 임시 파일 삭제 (선택 사항이지만 권장)
        if os.path.exists(video_file_path):
            os.remove(video_file_path)
            logging.info(f"Temporary video file deleted: {video_file_path}")

        return f"Video upload successful! ID: {response.get('id')}", 200
    except Exception as e:
        logging.error(f"Failed to upload video: {e}")
        # 에러 발생 시 HTTP 500 응답 반환
        return f"Failed to upload video: {str(e)}", 500
