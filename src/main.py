# src/main.py

import functions_framework
import logging
from .config import Config # .config로 변경
# from .youtube_uploader import YouTubeUploader # 필요시 주석 해제
# from .comment_poster import CommentPoster # 필요시 주석 해제

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 전역 Config 인스턴스 (함수 호출마다 다시 생성하지 않도록)
_config = None

def get_config():
    global _config
    if _config is None:
        try:
            logger.info("Config 인스턴스 생성 시도...")
            _config = Config()
            logger.info("Config 인스턴스 생성 성공.")
        except Exception as e:
            logger.critical(f"Config 인스턴스 생성 중 치명적인 오류 발생: {e}", exc_info=True)
            raise # 이 예외가 발생하면 함수 시작 자체가 실패합니다.
    return _config

@functions_framework.http
def youtube_automation_main(request):
    logger.info("함수 호출 시작: youtube_automation_main")

    try:
        config = get_config()

        # Secret Manager에서 API 키 가져오기 (필요할 때 호출)
        youtube_client_id = config.get_youtube_client_id()
        youtube_client_secret = config.get_youtube_client_secret()
        youtube_refresh_token = config.get_youtube_refresh_token()
        elevenlabs_api_key = config.get_elevenlabs_api_key()

        logger.info("모든 Secret Manager 값 로드 완료.")
        # logger.info(f"YouTube Client ID: {youtube_client_id[:5]}...") # 민감 정보는 마스킹해서 로깅
        # logger.info(f"ElevenLabs API Key: {elevenlabs_api_key[:5]}...") # 민감 정보는 마스킹해서 로깅

        # 여기에 나머지 로직 추가
        # 예: YouTubeUploader, CommentPoster 초기화 및 호출
        # uploader = YouTubeUploader(
        #     client_id=youtube_client_id,
        #     client_secret=youtube_client_secret,
        #     refresh_token=youtube_refresh_token,
        #     project_id=config.gcp_project_id,
        #     bucket_name=config.gcp_bucket_name
        # )
        # uploader.upload_video(...)

        response_message = "YouTube Shorts Automation 함수가 성공적으로 실행되었습니다."
        logger.info(response_message)
        return response_message, 200

    except Exception as e:
        logger.error(f"함수 실행 중 오류 발생: {e}", exc_info=True)
        return f"오류 발생: {e}", 500
