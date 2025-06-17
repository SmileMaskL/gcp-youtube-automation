# src/main.py

import logging
from pathlib import Path
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import config
from src.utils import setup_logging
from src.content_generator import generate_content
from src.tts_generator import text_to_speech
from src.bg_downloader import download_background_video
from src.video_creator import create_video_with_subtitles
from src.youtube_uploader import upload_to_youtube
from src.thumbnail_generator import create_thumbnail

def main():
    """
    YouTube 자동화 봇의 메인 실행 함수
    """
    setup_logging()
    logging.info("🚀 YouTube 자동화 프로세스를 시작합니다.")

    try:
        # 1. 콘텐츠 생성 (주제, 스크립트, 제목, 설명, 태그)
        logging.info("1단계: 콘텐츠 생성 시작...")
        # 생성할 콘텐츠의 주제를 자유롭게 변경해보세요.
        content = generate_content("여름철 건강을 지키는 예상 밖의 방법")
        
        # ★★★ 안정성 강화 ★★★
        # 콘텐츠 생성에 실패하면 프로세스를 중단합니다.
        if not content:
            logging.error("콘텐츠 생성에 실패하여 프로세스를 중단합니다.")
            sys.exit(1) # 오류 코드로 종료
        
        logging.info(f"✅ 콘텐츠 생성 완료! (제목: {content['title']})")

        # 2. TTS 오디오 생성
        logging.info("2단계: 음성(TTS) 생성 시작...")
        text_to_speech(content['script'], config.AUDIO_FILE_PATH)
        logging.info(f"✅ 음성 파일 저장 완료: {config.AUDIO_FILE_PATH}")

        # 3. 배경 비디오 다운로드
        logging.info("3단계: 배경 비디오 다운로드 시작...")
        video_query = content.get("video_query", "nature relaxing") # 쿼리가 없으면 기본값 사용
        download_background_video(video_query, config.OUTPUT_DIR)
        logging.info("✅ 배경 비디오 다운로드 완료!")

        # 4. 최종 비디오 생성 (자막 포함)
        logging.info("4단계: 최종 비디오 생성 시작...")
        background_video_path = next(config.OUTPUT_DIR.glob("background_*.mp4"))
        create_video_with_subtitles(
            background_video_path=background_video_path,
            audio_path=config.AUDIO_FILE_PATH,
            script_with_timing=content['script_with_timing'],
            output_path=config.VIDEO_FILE_PATH
        )
        logging.info(f"✅ 최종 비디오 생성 완료: {config.VIDEO_FILE_PATH}")

        # 5. 썸네일 생성
        logging.info("5단계: 썸네일 생성 시작...")
        thumbnail_text = content['title'].replace('\n', ' ')
        create_thumbnail(
            text=thumbnail_text,
            background_path=background_video_path,
            output_path=config.THUMBNAIL_FILE_PATH
        )
        logging.info(f"✅ 썸네일 생성 완료: {config.THUMBNAIL_FILE_PATH}")

        # 6. YouTube에 업로드
        logging.info("6단계: YouTube 업로드 시작...")
        upload_to_youtube(
            video_path=config.VIDEO_FILE_PATH,
            title=content['title'],
            description=content['description'],
            tags=content['tags'],
            thumbnail_path=config.THUMBNAIL_FILE_PATH
        )
        logging.info("✅ YouTube 업로드 성공!")

    except Exception as e:
        logging.error(f"❌ 프로세스 중 예측하지 못한 오류 발생: {e}", exc_info=True)
        sys.exit(1)

    logging.info("🎉 모든 프로세스가 성공적으로 완료되었습니다!")

if __name__ == "__main__":
    main()
