import logging
import os
import shutil # temp 폴더 전체 삭제를 위해 추가
from datetime import datetime
import time # 지연 시간 추가

from src.config import Config
from src.ai_rotation import ai_manager # 수정
from src.content_generator import ContentGenerator # 이름 변경
from src.tts_generator import generate_tts
from src.bg_downloader import download_background
from src.video_editor import create_short_video
from src.youtube_uploader import upload_youtube_short
from src.thumbnail_generator import generate_thumbnail # 새로 추가
from src.cleanup_manager import clean_local_temp_files, clean_gcp_bucket_files # 새로 추가

# 로그 설정
# 모든 로그를 logs/youtube_automation.log 파일에 기록
log_file_path = "logs/youtube_automation.log"
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler() # 콘솔에도 출력
    ]
)
logger = logging.getLogger(__name__)

def produce_single_short() -> bool:
    """단일 유튜브 쇼츠를 생성하고 업로드하는 전체 프로세스를 실행합니다."""
    try:
        # 1. 콘텐츠 생성 (트렌드 반영 및 AI 로테이션 포함)
        logger.info("1. 콘텐츠 생성 시작...")
        generator = ContentGenerator()
        content = generator.create_content()
        if not content:
            logger.error("콘텐츠 생성 실패: 유효한 콘텐츠를 얻지 못했습니다.")
            return False
        logger.info(f"콘텐츠 생성 완료. 제목: {content.get('title', 'N/A')}")
        
        # 2. 음성 생성
        logger.info("2. 음성 생성 시작...")
        audio_path = generate_tts(
            text=content['script'],
            voice_id=Config.get_elevenlabs_voice_id() # 수정
        )
        if not audio_path:
            logger.error("음성 생성 실패: 유효한 오디오 파일을 얻지 못했습니다.")
            return False
        logger.info(f"음성 생성 완료: {audio_path}")
        
        # 3. 배경 영상 다운로드
        logger.info("3. 배경 영상 다운로드 시작...")
        video_path = download_background(content['video_query'])
        if not video_path:
            logger.error("배경 영상 다운로드 실패: 유효한 비디오 파일을 얻지 못했습니다.")
            return False
        logger.info(f"배경 영상 다운로드 완료: {video_path}")
        
        # 4. 쇼츠 영상 제작
        logger.info("4. 쇼츠 영상 제작 시작...")
        output_video_filename = f"short_{int(datetime.now().timestamp())}.mp4"
        output_video_path = os.path.join("temp", output_video_filename)

        final_video_path = create_short_video(
            video_path=video_path,
            audio_path=audio_path,
            text=content['title'],
            font_path="fonts/Catfont.ttf",
            output_path=output_video_path # 추가: 출력 경로 지정
        )
        if not final_video_path:
            logger.error("쇼츠 영상 제작 실패: 유효한 출력 비디오 파일을 얻지 못했습니다.")
            return False
        logger.info(f"쇼츠 영상 제작 완료: {final_video_path}")

        # 5. 썸네일 자동 생성
        logger.info("5. 썸네일 자동 생성 시작...")
        thumbnail_filename = f"thumbnail_{int(datetime.now().timestamp())}.png"
        thumbnail_path = os.path.join("temp", thumbnail_filename)
        generated_thumbnail_path = generate_thumbnail(
            title=content['title'],
            output_path=thumbnail_path,
            font_path="fonts/Catfont.ttf"
        )
        if not generated_thumbnail_path:
            logger.warning("썸네일 생성 실패. 썸네일 없이 업로드 진행.")
            # 썸네일 생성 실패해도 업로드는 진행
        else:
            logger.info(f"썸네일 생성 완료: {generated_thumbnail_path}")
        
        # 6. 유튜브 업로드
        logger.info("6. 유튜브 업로드 시작...")
        upload_success = upload_youtube_short(
            file_path=final_video_path,
            title=content['title'],
            description=content['description'],
            tags=["쇼츠", "자동생성", "AI", "트렌드", content['video_query'].replace('_', ' '), "#" + content['title'].split(" ")[0] if content['title'].split(" ")[0] else ""] + content['description'].split("#")[1:] if "#" in content['description'] else [], # 태그 추가
            category_id="22", # People & Blogs (적절한 카테고리 ID로 변경 가능)
            privacy_status="public", # public, private, unlisted
            thumbnail_path=generated_thumbnail_path # 썸네일 경로 추가
        )
        
        if upload_success:
            logger.info(f"유튜브 쇼츠 업로드 성공: {content['title']}")
            # 업로드 성공 후 GCP 버킷에 저장 (선택 사항, 영구 보관용)
            # from google.cloud import storage
            # client = storage.Client()
            # bucket_name = os.getenv("GCP_BUCKET_NAME") # GitHub Secrets에 GCP_BUCKET_NAME 설정 필요
            # if bucket_name:
            #     bucket = client.bucket(bucket_name)
            #     blob = bucket.blob(f"uploaded_shorts/{os.path.basename(final_video_path)}")
            #     blob.upload_from_filename(final_video_path)
            #     logger.info(f"영상이 GCP 버킷 '{bucket_name}'에 저장되었습니다.")
            # else:
            #     logger.warning("GCP_BUCKET_NAME이 설정되지 않아 GCP 버킷에 영상을 저장하지 않습니다.")
            return True
        else:
            logger.error(f"유튜브 쇼츠 업로드 실패: {content['title']}")
            return False

    except Exception as e:
        logger.error(f"쇼츠 생성 및 업로드 프로세스 중 치명적인 오류 발생: {str(e)}", exc_info=True)
        return False
    finally:
        # 매 실행 후 임시 파일 정리 (로컬)
        logger.info("로컬 임시 파일 정리 시작...")
        clean_local_temp_files(retention_days=0) # 즉시 삭제
        # temp 폴더를 완전히 비우기 (더 확실하게)
        if os.path.exists("temp"):
            shutil.rmtree("temp")
            os.makedirs("temp", exist_ok=True)
            logger.info("temp/ 폴더를 완전히 비웠습니다.")


if __name__ == "__main__":
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    if not GCP_PROJECT_ID:
        logger.error("GCP_PROJECT_ID 환경 변수가 설정되지 않았습니다. 스크립트 실행을 중단합니다.")
        exit(1)
    
    # GitHub Actions에서 실행되므로 워크로드 아이덴티티 연동 설정을 가정합니다.
    # 로컬 테스트 시에는 GOOGLE_APPLICATION_CREDENTIALS 환경 변수를 설정해야 합니다.
    # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your/service-account-key.json"

    # 하루 총 5개 영상 생성 (GitHub Actions 스케줄과 독립적으로 동작)
    # GitHub Actions 스케줄 '0 3,7,12,18,22 * * *'에 따라 하루 최대 5번 실행됩니다.
    # 각 실행 시 produce_single_short() 한 번만 호출하도록 변경하여 GitHub Actions cron과 일치시킵니다.
    logger.info("유튜브 쇼츠 자동 생산 시스템 시작...")
    
    # GCP 버킷 파일 정리 (선택 사항, 필요시 활성화)
    # bucket_name = os.getenv("GCP_BUCKET_NAME")
    # if bucket_name:
    #     logger.info(f"GCP 버킷 '{bucket_name}' 파일 정리 시작...")
    #     clean_gcp_bucket_files(bucket_name=bucket_name, retention_days=7) # 7일보다 오래된 파일 삭제

    success_count = 0
    # produce_single_short()는 GitHub Actions의 단일 작업 실행에 맞춰 한 번만 호출됩니다.
    # 만약 GitHub Actions가 하루에 5번 실행되도록 cron을 설정했다면,
    # 이 부분에서 루프를 돌릴 필요 없이 한 번만 호출하면 됩니다.
    # 현재 GitHub Actions의 cron 설정은 하루 5회 실행되므로,
    # 여기서는 produce_single_short()를 한 번만 호출하도록 합니다.
    if produce_single_short():
        success_count += 1
        logger.info("단일 쇼츠 생성 및 업로드 성공.")
    else:
        logger.error("단일 쇼츠 생성 및 업로드 실패.")

    logger.info(f"총 {success_count}개의 쇼츠 생성 및 업로드 완료.")
    
    # 최종적으로 로컬 임시 파일 정리 확인
    clean_local_temp_files(retention_days=0)
    logger.info("모든 프로세스 완료.")
