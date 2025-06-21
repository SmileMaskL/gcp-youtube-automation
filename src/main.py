# src/main.py (전체 코드)

import os
import json
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Cloud Functions HTTP 트리거를 위해 반드시 필요
import functions_framework

# src 폴더 내부의 다른 모듈 임포트
from src.config import config # config.py에서 config 객체를 임포트합니다.
from src.content_generator import ContentGenerator
from src.tts_generator import TTSGenerator
from src.video_creator import VideoCreator
from src.youtube_uploader import YouTubeUploader
from src.cleanup_manager import CleanupManager
from src.monitoring import Monitoring
from src.ai_rotation import AIRotation
from src.comment_poster import CommentPoster
from src.shorts_converter import ShortsConverter
from src.thumbnail_generator import ThumbnailGenerator
from src.error_handler import ErrorHandler
from src.utils import Utils
# 필요한 경우 다른 모듈도 여기에 임포트합니다.

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 스레드 풀 초기화 (비동기 작업을 위해)
# Cloud Functions 환경에서는 필요에 따라 조절하거나 제거할 수 있습니다.
# 여기서는 병렬 작업을 위해 유지합니다.
executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 1)

async def youtube_automation_main_logic():
    """
    YouTube Shorts 자동화의 핵심 로직을 실행하는 비동기 함수.
    """
    logger.info("YouTube 자동화 프로세스 시작.")

    error_handler = ErrorHandler(config) # 에러 핸들러 초기화

    try:
        # 모니터링 객체 초기화 (Cloud Logging에 정보 전송)
        monitoring = Monitoring(config.gcp_project_id, config.gcp_bucket_name, 'youtube-shorts-automation')

        # API 키 로테이션 및 사용량 관리 (중요!)
        # Secret Manager에서 가져온 키는 config 객체에 이미 설정되어 있어야 합니다.
        ai_rotation = AIRotation(
            openai_keys_json_path=config.openai_keys_json_path,
            gemini_api_key_secret_name=config.gemini_api_key_secret_name,
            google_api_key_secret_name=config.google_api_key_secret_name,
            news_api_key_secret_name=config.news_api_key_secret_name,
            pexel_api_key_secret_name=config.pexel_api_key_secret_name,
            project_id=config.gcp_project_id,
            quota_limit_per_day=config.api_quota_per_day, # 일일 API 사용량 한도
            quota_limit_per_month=config.api_quota_per_month # 월간 API 사용량 한도
        )
        await ai_rotation.initialize_api_keys() # Secret Manager에서 키 로드 및 초기화
        # 현재 활성화된 API 키를 config 객체에 반영
        config.openai_api_key = ai_rotation.get_current_openai_key()
        config.gemini_api_key = ai_rotation.get_current_gemini_key()
        config.google_api_key = ai_rotation.get_current_google_key()
        config.news_api_key = ai_rotation.get_current_news_key()
        config.pexels_api_key = ai_rotation.get_current_pexels_key()
        # ElevenLabs는 현재 env var로 직접 설정하므로 따로 로테이션하지 않음.
        # 필요시 ElevenLabs API 키도 Secret Manager에서 관리하도록 변경 가능.
        
        # 일일 및 월간 쿼터 체크
        if not await ai_rotation.can_proceed_with_daily_quota():
            logger.warning("일일 API 쿼터 초과. 다음 실행을 기다립니다.")
            monitoring.log_info("Daily API quota exceeded. Skipping execution.", {'status': 'skipped', 'reason': 'daily_quota'})
            return {"status": "skipped", "reason": "daily_quota_exceeded"}

        if not await ai_rotation.can_proceed_with_monthly_quota():
            logger.warning("월간 API 쿼터 초과. 다음 달까지 기다립니다.")
            monitoring.log_info("Monthly API quota exceeded. Skipping execution.", {'status': 'skipped', 'reason': 'monthly_quota'})
            return {"status": "skipped", "reason": "monthly_quota_exceeded"}

        # 주요 구성 요소 초기화
        content_generator = ContentGenerator(config.gemini_api_key, config.google_api_key, config.news_api_key)
        tts_generator = TTSGenerator(config.elevenlabs_api_key, config.elevenlabs_voice_id)
        video_creator = VideoCreator(config.gcp_bucket_name, config.pexels_api_key)
        youtube_uploader = YouTubeUploader(
            config.gcp_project_id,
            config.gcp_bucket_name,
            config.youtube_oauth_credentials_secret_name
        )
        comment_poster = CommentPoster(config.youtube_oauth_credentials_secret_name)
        shorts_converter = ShortsConverter()
        thumbnail_generator = ThumbnailGenerator(config.gemini_api_key) # 썸네일 생성기 초기화

        # 1. 컨텐츠 생성 (AI 로테이션 적용)
        topic = await content_generator.generate_topic()
        logger.info(f"선택된 토픽: {topic}")
        script = await content_generator.generate_script(topic)
        logger.info("스크립트 생성 완료.")

        # API 사용량 트래킹 (실제 사용량에 따라 cost 조절 필요)
        # content_generator에서 사용된 API 비용을 추적
        ai_rotation.track_api_usage("gemini", cost=0.01) # 예시 비용, 실제 API 사용량에 따라 정확히 계산 필요

        # 2. 음성 생성
        audio_path = await tts_generator.generate_tts(script, "temp_audio.mp3")
        logger.info(f"음성 파일 생성 완료: {audio_path}")

        # 3. 비디오 생성 (배경 영상 다운로드 및 편집)
        video_path = await video_creator.create_video(script, audio_path, "temp_video.mp4")
        logger.info(f"최종 비디오 생성 완료: {video_path}")

        # 4. 썸네일 자동 생성
        thumbnail_path = await thumbnail_generator.generate_thumbnail(topic, script, "temp_thumbnail.jpg")
        logger.info(f"썸네일 생성 완료: {thumbnail_path}")

        # 5. YouTube Shorts 업로드
        title = f"AI 생성 쇼츠: {topic[:50]}..." # 제목 너무 길면 잘라냄
        description = script # 스크립트를 설명으로 사용
        tags = [tag.strip() for tag in topic.split()[:5]] # 토픽에서 태그 추출 (최대 5개)

        # 동영상 및 썸네일 업로드
        video_id = await youtube_uploader.upload_video(
            video_path,
            title,
            description,
            tags,
            thumbnail_path # 생성된 썸네일 경로 전달
        )
        logger.info(f"YouTube Shorts 업로드 완료. 비디오 ID: {video_id}")

        # 6. 댓글 자동 작성 (선택 사항)
        if video_id:
            await comment_poster.post_comment(video_id, "AI로 자동 생성된 Shorts입니다. 구독과 좋아요 부탁드려요!")
            logger.info("댓글 작성 완료.")

        # 7. 사용량 및 쿼터 업데이트
        await ai_rotation.increment_daily_usage()
        await ai_rotation.increment_monthly_usage()
        await ai_rotation.save_usage_data() # 사용량 데이터 저장

        monitoring.log_info(f"YouTube 자동화 프로세스 성공적으로 완료. 비디오 ID: {video_id}",
                             {'status': 'success', 'video_id': video_id, 'topic': topic})

        # 임시 파일 정리 (중요!)
        cleanup_manager = CleanupManager()
        cleanup_manager.add_file(audio_path)
        cleanup_manager.add_file(video_path)
        cleanup_manager.add_file(thumbnail_path)
        cleanup_manager.cleanup_temp_files()
        logger.info("임시 파일 정리 완료.")

        return {"status": "success", "video_id": video_id}

    except Exception as e:
        error_info = error_handler.handle_error(e)
        logger.error(f"YouTube 자동화 프로세스 중 오류 발생: {error_info}", exc_info=True)
        monitoring.log_error(f"YouTube 자동화 프로세스 중 오류 발생: {e}", {'error_type': type(e).__name__, 'error_message': str(e)})
        raise # Cloud Function 오류로 전파

@functions_framework.http
def youtube_automation_main(request):
    """
    Cloud Function의 HTTP 트리거 엔트리포인트.
    HTTP 요청을 처리하고, 비동기 YouTube 자동화 로직을 실행합니다.
    """
    logger.info("Cloud Function (youtube_automation_main) 호출됨.")

    # 요청 본문에서 'daily_run' 플래그를 확인하여 수동 실행/스케줄 실행 구분
    # 이 부분은 스케줄러 (Cloud Scheduler)나 외부에서 호출할 때 사용될 수 있습니다.
    request_json = request.get_json(silent=True)
    is_scheduled_run = request_json and isinstance(request_json, dict) and request_json.get('daily_run')

    if is_scheduled_run:
        logger.info("일일 자동 실행 요청 감지. 로직 실행 시작.")
    else:
        logger.info("일반 HTTP 요청. 함수 로직 실행 대기.")

    try:
        # 비동기 로직 실행 및 완료 대기
        # Cloud Functions는 비동기 함수를 지원하지만, HTTP 트리거는 동기 응답을 기대합니다.
        # 따라서 asyncio.run을 사용하여 비동기 함수를 동기적으로 실행합니다.
        # 단, Flask request context 밖에서 실행되도록 주의해야 합니다.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(youtube_automation_main_logic())
        loop.close()
        return {"message": "YouTube automation initiated successfully", "result": result}, 200
    except Exception as e:
        logger.error(f"YouTube 자동화 로직 실행 중 오류 발생: {e}", exc_info=True)
        return {"error": f"YouTube automation failed: {str(e)}"}, 500
