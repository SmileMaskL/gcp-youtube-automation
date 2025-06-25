# src/main.py

import functions_framework
import os
import logging
from datetime import datetime
import random
from flask import Request, jsonify # Flask Request 객체를 명시적으로 임포트
import subprocess # FFmpeg 경로 확인을 위해 추가

# FFmpeg 경로를 PATH 환경 변수에 추가
# Cloud Functions 환경에서 ./bin/ffmpeg 경로를 인식하도록 설정
os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), "bin")

# FFmpeg 경로 확인용 로깅 (배포 후 로그에서 이 메시지를 확인해보세요)
logging.info(f"Updated PATH: {os.environ['PATH']}")
try:
    import subprocess
    subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
    logging.info("FFmpeg found and working!")
except Exception as e:
    logging.error(f"FFmpeg not found or not working: {e}")
    logging.error(f"FFmpeg stderr: {e.stderr.decode()}") # stderr 내용도 출력

# 로그 설정을 맨 위로 옮겨서 함수 시작부터 로그를 볼 수 있도록 합니다.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- FFmpeg 바이너리 경로 설정 (핵심!) ---
# Cloud Functions 컨테이너 내부에서는 'src' 폴더가 '/workspace/src'에 해당합니다.
# 따라서 우리가 만든 'bin' 폴더는 '/workspace/src/bin'이 됩니다.
FFMPEG_BIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin')

# PATH 환경 변수에 FFmpeg 바이너리 경로를 추가하여 시스템이 'ffmpeg' 명령어를 찾을 수 있게 합니다.
os.environ["PATH"] += os.pathsep + FFMPEG_BIN_DIR
# moviepy나 imageio-ffmpeg이 FFmpeg 실행 파일을 찾을 수 있도록 명시적으로 알려줍니다.
os.environ["IMAGEIO_FFMPEG_EXE"] = os.path.join(FFMPEG_BIN_DIR, "ffmpeg")

logger.info(f"FFmpeg binary path added to PATH: {FFMPEG_BIN_DIR}")

try:
    # FFmpeg이 정상적으로 실행되는지 확인 (디버깅에 매우 유용)
    # 이 부분이 실패하면 'Container Healthcheck failed'의 원인일 가능성이 매우 높습니다.
    ffmpeg_path = os.path.join(FFMPEG_BIN_DIR, "ffmpeg")
    if not os.path.exists(ffmpeg_path):
        raise FileNotFoundError(f"FFmpeg executable not found at {ffmpeg_path}")
    
    # 실행 권한 확인 (Cloud Functions 환경에서는 이미 부여되어야 함)
    # 로컬에서 chmod +x 를 했다면, 여기에선 추가적인 권한 부여는 필요 없지만, 존재 유무 확인은 중요.
    if not os.access(ffmpeg_path, os.X_OK):
        raise PermissionError(f"FFmpeg executable at {ffmpeg_path} does not have execute permission.")

    result = subprocess.run([ffmpeg_path, "-version"],
                            check=True, capture_output=True, text=True)
    logger.info(f"FFmpeg found and working. Version info: {result.stdout.splitlines()[0]}")
except FileNotFoundError as e:
    logger.critical(f"CRITICAL ERROR: {e}. FFmpeg binary is missing or path is incorrect. "
                    "This will cause health check failure.")
    # 실제 프로덕션에서는 이 에러 시 바로 종료되도록 할 수도 있습니다.
    # 하지만 헬스체크 응답을 위해 일단 함수가 계속 진행되도록 합니다.
except PermissionError as e:
    logger.critical(f"CRITICAL ERROR: {e}. FFmpeg binary does not have execute permission. "
                    "Please ensure chmod +x was applied.")
except subprocess.CalledProcessError as e:
    logger.critical(f"CRITICAL ERROR: FFmpeg command failed with error: {e.stderr}", exc_info=True)
except Exception as e:
    logger.critical(f"CRITICAL ERROR: An unexpected error occurred while checking FFmpeg: {e}", exc_info=True)

# src/ 디렉토리 내의 커스텀 모듈들을 임포트합니다.
# 반드시 점(.)을 사용하여 상대 경로로 임포트해야 합니다.
# 그렇지 않으면 Cloud Functions 컨테이너 내부에서 모듈을 찾지 못할 수 있습니다.
from .config import Config
from .youtube_uploader import upload_video
from .ai_manager import generate_niche_content
from .tts_generator import generate_tts_audio
from .video_creator import create_short_video
from .video_editor import edit_video_for_shorts
from .bg_downloader import download_background_video


@functions_framework.http
def trigger_youtube_upload(request: Request):
    """
    HTTP 요청을 받아 YouTube 동영상 업로드 프로세스를 시작합니다.
    이 함수는 Cloud Functions의 주 진입점이며, 모든 로직을 직접 수행합니다.
    Flask Request 객체를 사용하여 요청 데이터를 처리합니다.
    """
    logger.info(f"--- Cloud Function '{request.path}' ({request.method}) 시작 ---")

    # --- Cloud Functions 2세대 (Cloud Run 기반) 헬스체크 처리 (중요!) ---
    # Cloud Run은 배포된 컨테이너의 활성 상태를 확인하기 위해
    # 기본적으로 '/' 경로로 HTTP GET 요청을 보냅니다.
    # 이 요청에 대해 200 OK 응답을 주지 않으면 'Container Healthcheck failed' 에러가 발생합니다.
    # 이 로직은 함수 시작 시 가장 먼저 실행되어야 합니다.
    if request.method == 'GET' and request.path == '/':
        logger.info("Healthcheck request received at '/'. Responding with 200 OK.")
        return "OK", 200

    # 실제 자동화 로직은 POST 요청 시에만 실행됩니다.
    # Cloud Scheduler는 HTTP POST 요청을 보낼 것입니다.
    if request.method != 'POST':
        logger.warning(f"Unsupported HTTP method: {request.method}. Only POST is supported for triggering.")
        return "Unsupported method. Please use POST to trigger video generation.", 405

    # 이제 실제 YouTube 자동화 로직을 실행합니다.
    try:
        project_id = os.environ.get("GCP_PROJECT_ID")
        bucket_name = os.environ.get("GCP_BUCKET_NAME")

        if not project_id or not bucket_name:
            logger.error("GCP_PROJECT_ID 또는 GCP_BUCKET_NAME 환경 변수가 설정되지 않았습니다.")
            return "설정 오류: 필수 환경 변수 누락.", 500

        config = Config(project_id=project_id, bucket_name=bucket_name)

        elevenlabs_api_key = config.get_elevenlabs_api_key()
        elevenlabs_voice_id = config.elevenlabs_voice_id
        pexels_api_key = config.get_pexels_api_key()

        logger.info("API 키 및 설정 로드 완료.")

    except Exception as e:
        logger.error(f"설정 또는 시크릿 로드 실패: {e}", exc_info=True)
        return f"설정 오류: {str(e)}", 500

    # Cloud Functions는 /tmp 디렉토리만 쓰기 가능합니다.
    temp_dir = "/tmp"
    os.makedirs(temp_dir, exist_ok=True) # 혹시 없을 경우를 대비하여 생성

    niche_keywords = ["신기한 과학 사실", "역사 속 숨겨진 이야기", "최신 기술 트렌드",
                      "일상 속 꿀팁", "건강 상식"]
    selected_niche = random.choice(niche_keywords)

    ai_model_preference = random.choice(["gemini", "openai"])

    content_topic = ""
    suggested_title = ""

    try:
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
            logger.warning(f"AI 응답 형식이 예상과 다릅니다: {ai_response}. "
                           f"기본 콘텐츠 사용.")
            content_topic = ("자동 생성된 유튜브 쇼츠 영상입니다. "
                             "콘텐츠 생성에 문제가 있었습니다.")
            suggested_title = "자동 생성 오류 쇼츠"

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
        _cleanup_temp_files(temp_dir)
        return f"TTS 오류: {str(e)}", 500

    background_video_path = os.path.join(temp_dir, "background_video.mp4")
    pexels_query = selected_niche.split(' ')[0] if selected_niche else "abstract"
    try:
        download_background_video(pexels_api_key, pexels_query, background_video_path)
        logger.info(f"배경 영상 다운로드 완료: {background_video_path}")
    except Exception as e:
        logger.error(f"배경 영상 다운로드 실패: {e}", exc_info=True)
        _cleanup_temp_files(temp_dir)
        return f"배경 영상 다운로드 오류: {str(e)}", 500

    final_video_filename = (f"youtube_short_"
                            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
    final_video_file_path = os.path.join(temp_dir, final_video_filename) # /tmp에 저장

    try:
        created_video_path = create_short_video(background_video_path,
                                                audio_file_path,
                                                os.path.join(temp_dir,
                                                             "temp_created_video.mp4"))
        logger.info(f"기본 영상 생성 완료: {created_video_path}")

        edited_video_path = edit_video_for_shorts(created_video_path,
                                                  content_topic, suggested_title)
        
        # moviepy의 write_videofile은 기본적으로 현재 작업 디렉토리에 저장하므로,
        # temp_dir에 최종 파일로 저장하도록 명시적으로 처리합니다.
        # edited_video_path가 이미 /tmp 내의 경로라면 os.rename은 불필요할 수 있지만,
        # 안전을 위해 최종 경로로 옮기는 로직은 유지합니다.
        if os.path.dirname(edited_video_path) != temp_dir:
            temp_edited_path = os.path.join(temp_dir, os.path.basename(edited_video_path))
            os.rename(edited_video_path, temp_edited_path)
            edited_video_path = temp_edited_path

        os.rename(edited_video_path, final_video_file_path)
        logger.info(f"최종 쇼츠 영상 편집 완료 및 저장: {final_video_file_path}")

    except Exception as e:
        logger.error(f"영상 제작 또는 편집 실패: {e}", exc_info=True)
        _cleanup_temp_files(temp_dir)
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
    video_category_id = "22" # YouTube에서 '블로그/사람들' 카테고리 ID
    video_privacy_status = "public" # public, private, unlisted 중 선택 가능

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

        _cleanup_temp_files(temp_dir)

        logger.info("--- Cloud Function 'trigger_youtube_upload' 완료 ---")
        return f"Video upload successful! ID: {response.get('id')}", 200

    except Exception as e:
        logger.error(f"최종 YouTube 업로드 실패: {e}", exc_info=True)
        _cleanup_temp_files(temp_dir)
        return f"YouTube 업로드 오류: {str(e)}", 500

def _cleanup_temp_files(temp_dir):
    """
    지정된 임시 디렉토리의 모든 파일을 삭제합니다.
    """
    for f in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, f)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                logger.info(f"임시 파일 삭제: {file_path}")
            except Exception as cleanup_e:
                logger.warning(f"임시 파일 삭제 실패: {file_path}, {cleanup_e}")
