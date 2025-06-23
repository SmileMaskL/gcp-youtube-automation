# src/main.py

import functions_framework
import os
import logging
from datetime import datetime
import random

from config import Config
from youtube_uploader import upload_video
from ai_manager import generate_niche_content
from tts_generator import generate_tts_audio
from video_creator import create_short_video
from video_editor import edit_video_for_shorts
from bg_downloader import download_background_video

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@functions_framework.http
def trigger_youtube_upload(request):
    logger.info("--- Cloud Function 'trigger_youtube_upload' 시작 ---")

    try:
        project_id = os.environ.get("GCP_PROJECT_ID")
        bucket_name = os.environ.get("GCP_BUCKET_NAME")

        config = Config(project_id=project_id, bucket_name=bucket_name)

        # gemini_api_key는 ai_manager 내부에서 config를 통해 직접 접근하므로,
        # 여기서는 사용되지 않습니다. 따라서 F841 경고를 피하기 위해 주석 처리합니다.
        # gemini_api_key = config.get_gemini_api_key()
        elevenlabs_api_key = config.get_elevenlabs_api_key()
        elevenlabs_voice_id = config.elevenlabs_voice_id
        pexels_api_key = config.get_pexels_api_key()

        logger.info("API 키 및 설정 로드 완료.")

    except Exception as e:
        logger.error(f"설정 또는 시크릿 로드 실패: {e}", exc_info=True)
        return f"설정 오류: {str(e)}", 500

    temp_dir = "/tmp"
    os.makedirs(temp_dir, exist_ok=True)

    niche_keywords = ["신기한 과학 사실", "역사 속 숨겨진 이야기", "최신 기술 트렌드",
                      "일상 속 꿀팁", "건강 상식"]
    selected_niche = random.choice(niche_keywords)

    ai_model_preference = random.choice(["gemini", "openai"])

    content_topic = ""
    suggested_title = ""

    try:
        # E501 해결: 줄 길이를 79자 이하로 맞춤
        logger.info(f"선택된 틈새 키워드: '{selected_niche}', "
                    f"AI 모델 선호: '{ai_model_preference}'")

        ai_response = generate_niche_content(config, selected_niche,
                                             ai_model_preference)

        if (isinstance(ai_response, dict) and "content" in ai_response and
                "title" in ai_response):
            content_topic = ai_response.get("content", "생성된 콘텐츠가 없습니다.")
            suggested_title = ai_response.get("title", "흥미로운 쇼츠")
            if len(content_topic) > 200:
                content_topic = content_topic[:200] + "..."
        else:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.warning(f"AI 응답 형식이 예상과 다릅니다: {ai_response}. "
                           f"기본 콘텐츠 사용.")
            content_topic = ("자동 생성된 유튜브 쇼츠 영상입니다. "
                             "콘텐츠 생성에 문제가 있었습니다.")
            suggested_title = "자동 생성 오류 쇼츠"

        # E501 해결: 줄 길이를 79자 이하로 맞춤
        logger.info(f"콘텐츠 생성 완료. 제목: '{suggested_title}', "
                    f"내용: '{content_topic[:50]}...'")

    except Exception as e:
        logger.error(f"AI 콘텐츠 생성 실패: {e}", exc_info=True)
        content_topic = ("자동 생성된 유튜브 쇼츠 영상입니다. "
                         "콘텐츠 생성 중 오류가 발생했습니다.")
        suggested_title = "AI 생성 실패 쇼츠"

    audio_file_path = os.path.join(temp_dir, "generated_audio.mp3")
    try:
        generate_tts_audio(elevenlabs_api_key, content_topic,
                           elevenlabs_voice_id, audio_file_path)
        logger.info(f"음성 파일 생성 완료: {audio_file_path}")
    except Exception as e:
        logger.error(f"TTS 음성 생성 실패: {e}", exc_info=True)
        return f"TTS 오류: {str(e)}", 500

    background_video_path = os.path.join(temp_dir, "background_video.mp4")
    pexels_query = selected_niche.split(' ')[0] if selected_niche else "abstract"
    try:
        download_background_video(pexels_api_key, pexels_query, background_video_path)
        logger.info(f"배경 영상 다운로드 완료: {background_video_path}")
    except Exception as e:
        logger.error(f"배경 영상 다운로드 실패: {e}", exc_info=True)
        return f"배경 영상 다운로드 오류: {str(e)}", 500


    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    final_video_filename = (f"youtube_short_"
                            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
    final_video_file_path = os.path.join(output_dir, final_video_filename)

    try:
        created_video_path = create_short_video(background_video_path,
                                                audio_file_path,
                                                os.path.join(temp_dir,
                                                            "temp_created_video.mp4"))
        logger.info(f"기본 영상 생성 완료: {created_video_path}")

        edited_video_path = edit_video_for_shorts(created_video_path,
                                                  content_topic, suggested_title)
        os.rename(edited_video_path, final_video_file_path)
        logger.info(f"최종 쇼츠 영상 편집 완료 및 저장: {final_video_file_path}")

    except Exception as e:
        logger.error(f"영상 제작 또는 편집 실패: {e}", exc_info=True)
        return f"영상 제작 오류: {str(e)}", 500

    video_title_for_upload = suggested_title
    video_description = (
        f"AI가 자동으로 생성하고 업로드한 유튜브 쇼츠입니다.\n\n"
        f"주제: {selected_niche}\n"
        f"콘텐츠: {content_topic}\n\n"
        f"#AI #유튜브쇼츠 #자동생성 #shorts #viral "
        f"#{selected_niche.replace(' ', '')}"
    )
    video_tags = [tag.strip() for tag in
                  (f"shorts,AI,자동화,유튜브,꿀팁,수익화,정보,{selected_niche},"
                   f"{suggested_title.replace(' ', '')}").split(',') if tag.strip()]
    video_category_id = "22"
    video_privacy_status = "public"

    try:
        response = upload_video(
            final_video_file_path,
            video_title_for_upload,
            video_description,
            video_tags,
            video_category_id,
            video_privacy_status,
            config_instance=config
        )
        logger.info(f"영상 업로드 성공! YouTube ID: {response.get('id')}")

        for f in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
                logger.info(f"임시 파일 삭제: {file_path}")

        logger.info("--- Cloud Function 'trigger_youtube_upload' 완료 ---")
        return f"Video upload successful! ID: {response.get('id')}", 200

    except Exception as e:
        logger.error(f"최종 YouTube 업로드 실패: {e}", exc_info=True)
        return f"YouTube 업로드 오류: {str(e)}", 500
    
