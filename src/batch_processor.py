import os
import json
import time
import random
from datetime import datetime, timedelta
import logging



# 로깅 설정
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("youtube_automation.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

# 다른 모듈 임포트 (src/ 폴더 내 파일들)
from src.config import Config
from src.error_handler import retry_on_failure
from src.usage_tracker import check_quota, update_usage, get_max_limit
from src.trend_api import get_trending_news # News API 연동
from src.content_generator import generate_content_with_ai # AI 로테이션 적용
from src.tts_generator import generate_audio
from src.bg_downloader import download_background_video
from src.video_creator import create_video
from src.thumbnail_generator import generate_thumbnail
from src.youtube_uploader import upload_video, refresh_youtube_oauth_token
from src.comment_poster import post_comment
from src.cleanup_manager import cleanup_old_files

if os.environ.get("PORT") is not None:
    logger.info(f"Ignoring PORT: {os.environ['PORT']}")

def main_batch_process():
    logger.info("🎬 YouTube Automation Batch Process Started!")

    # 1. 설정 로드 (환경 변수 또는 .env 파일)
    # Cloud Run 환경에서는 환경 변수가 우선적으로 로드됩니다.
    # 로컬 테스트 시에는 .env 파일이 사용됩니다.
    config = Config()
    logger.info(f"Loaded config: Project ID={config.GCP_PROJECT_ID}, Bucket Name={config.GCP_BUCKET_NAME}")

    # 2. YouTube OAuth 토큰 새로고침 (만료 방지)
    # 깃허브 시크릿에서 가져온 YOUTUBE_OAUTH_CREDENTIALS 값을 사용합니다.
    try:
        updated_credentials_json = retry_on_failure(lambda: refresh_youtube_oauth_token(config.YOUTUBE_OAUTH_CREDENTIALS))
        config.YOUTUBE_OAUTH_CREDENTIALS = updated_credentials_json
        logger.info("YouTube OAuth token refreshed successfully.")
        # 업데이트된 자격증명을 환경 변수로 다시 설정 (다음 작업에 사용)
        # 이 부분은 실제 GCP Secret Manager에 업데이트하는 로직이 필요할 수 있으나
        # Cloud Run Job은 단발성 실행이므로, 메모리에서만 업데이트하고 다음 실행 시 새롭게 로드합니다.
    except Exception as e:
        logger.error(f"Failed to refresh YouTube OAuth token: {e}")
        # 중요한 오류이므로, 여기서 프로세스 중단 또는 알림 전송 고려
        return

    # 3. API 쿼터 초기화 및 로딩
    # API 사용량은 Cloud Run Job 실행 시마다 초기화되므로,
    # 장기적인 쿼터 관리는 Secret Manager에 저장된 값을 읽어오거나 외부 DB 사용 필요
    # 여기서는 간단하게 이 세션 내에서만 사용량 추적
    daily_api_usage = {
        "gemini": 0,
        "openai": 0,
        "elevenlabs": 0,
        "pexels": 0,
        "youtube": 0,
        "news_api": 0
    }
    
    # 4. 일일 5개 영상 생성을 위한 루프
    num_videos_to_create = 5
    for i in range(num_videos_to_create):
        logger.info(f"✨ Starting video generation process {i+1}/{num_videos_to_create}")

        try:
            # 4-1. 핫이슈 뉴스 가져오기
            logger.info("Fetching trending news...")
            trending_topic = retry_on_failure(lambda: get_trending_news(config.NEWS_API_KEY))
            if not trending_topic:
                logger.warning("No trending topic found. Skipping video generation.")
                continue
            logger.info(f"Trending topic for video {i+1}: {trending_topic}")
            update_usage("news_api", 1) # News API 사용량 업데이트
            check_quota("news_api", daily_api_usage["news_api"])


            # 4-2. AI를 사용하여 콘텐츠 (스크립트, 제목, 설명, 태그, 댓글) 생성 (Gemini & OpenAI 로테이션)
            logger.info("Generating content using AI (Gemini/OpenAI rotation)...")
            ai_choice = "gemini" if daily_api_usage["gemini"] < get_max_limit("gemini") else "openai"
            if ai_choice == "openai" and daily_api_usage["openai"] >= get_max_limit("openai"):
                 logger.warning("Both Gemini and OpenAI API quotas exceeded or near limit. Skipping this video.")
                 continue # 두 API 모두 한도 초과 시 다음 영상으로 넘어감

            generated_content = retry_on_failure(
                lambda: generate_content_with_ai(
                    ai_choice,
                    trending_topic,
                    config.GEMINI_API_KEY,
                    config.OPENAI_KEYS_JSON # JSON 문자열 형태로 전달
                )
            )
            update_usage(ai_choice, 1) # AI API 사용량 업데이트
            check_quota(ai_choice, daily_api_usage[ai_choice])


            script = generated_content.get("script", "Generated script is empty.")
            video_title = generated_content.get("title", f"자동 생성 영상 {datetime.now().strftime('%Y%m%d_%H%M%S')}")
            video_description = generated_content.get("description", "자동 생성된 영상입니다.")
            video_tags = generated_content.get("tags", "자동생성,shorts,핫이슈").split(',')
            auto_comment = generated_content.get("comment", "흥미로운 영상이네요!")

            if not script:
                logger.error("Generated script is empty. Skipping video generation.")
                continue

            logger.info(f"Video {i+1} Title: {video_title}")

            # 4-3. ElevenLabs로 음성 생성
            logger.info("Generating audio with ElevenLabs...")
            audio_output_path = f"output/audio_{i}.mp3"
            retry_on_failure(lambda: generate_audio(script, audio_output_path, config.ELEVENLABS_API_KEY, config.ELEVENLABS_VOICE_ID))
            logger.info(f"Audio generated at {audio_output_path}")
            update_usage("elevenlabs", len(script)) # 글자 수에 비례하여 사용량 업데이트
            check_quota("elevenlabs", daily_api_usage["elevenlabs"])

            # 4-4. Pexels에서 배경 영상 다운로드
            logger.info("Downloading background video from Pexels...")
            video_query = trending_topic.split(' ')[0] # 키워드에서 첫 단어 사용
            background_video_path = f"output/bg_video_{i}.mp4"
            retry_on_failure(lambda: download_background_video(video_query, background_video_path, config.PEXELS_API_KEY))
            logger.info(f"Background video downloaded to {background_video_path}")
            update_usage("pexels", 1)
            check_quota("pexels", daily_api_usage["pexels"])

            # 4-5. 최종 영상 생성 (고양이체.ttf 폰트 사용)
            logger.info("Creating final video...")
            final_video_path = f"output/final_video_{i}.mp4"
            font_path = "/app/fonts/Catfont.ttf" # Dockerfile에서 복사된 경로
            retry_on_failure(lambda: create_video(background_video_path, audio_output_path, final_video_path, font_path=font_path))
            logger.info(f"Final video created at {final_video_path}")

            # 4-6. 썸네일 자동 생성
            logger.info("Generating thumbnail...")
            thumbnail_path = f"output/thumbnail_{i}.jpg"
            retry_on_failure(lambda: generate_thumbnail(final_video_path, thumbnail_path, video_title))
            logger.info(f"Thumbnail created at {thumbnail_path}")

            # 4-7. YouTube에 영상 업로드
            logger.info("Uploading video to YouTube...")
            # YouTube API 쿼터 관리
            check_quota("youtube", daily_api_usage["youtube"])
            video_id = retry_on_failure(
                lambda: upload_video(
                    final_video_path,
                    video_title,
                    video_description,
                    video_tags,
                    config.YOUTUBE_OAUTH_CREDENTIALS,
                    thumbnail_path
                )
            )
            update_usage("youtube", 1)
            logger.info(f"Video uploaded successfully! Video ID: {video_id}")
            
            # 4-8. YouTube 댓글 자동 작성
            if video_id:
                logger.info("Posting comment to YouTube video...")
                retry_on_failure(lambda: post_comment(video_id, auto_comment, config.YOUTUBE_OAUTH_CREDENTIALS))
                logger.info("Comment posted successfully!")

            # 모든 단계 성공 시, 임시 파일 정리 (버킷 사용량 관리)
            cleanup_old_files(config.GCP_BUCKET_NAME, hours_to_keep=1) # 1시간 지난 파일 정리
            logger.info(f"Temporary files for video {i+1} cleaned up in Cloud Storage.")

            logger.info(f"✅ Video {i+1} generation and upload completed!")
            time.sleep(10) # 다음 영상 생성 전 잠시 대기
            
        except Exception as e:
            logger.error(f"❌ Error during video {i+1} processing: {e}", exc_info=True)
            # 오류 발생 시에도 임시 파일 정리 시도
            cleanup_old_files(config.GCP_BUCKET_NAME, hours_to_keep=1)

    logger.info("🎉 YouTube Automation Batch Process Finished!")

if __name__ == "__main__":
    main_batch_process()
