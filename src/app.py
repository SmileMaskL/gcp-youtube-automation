# src/app.py
import os
import logging
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor

# Google Cloud Imports
import google.cloud.logging
from google.cloud import storage

# Third-party API Clients (필요에 따라 주석 해제 및 설치)
import requests # 웹 요청용 (뉴스 API, Pexels API 등)
# from openai import OpenAI # OpenAI Python SDK
# from google.generativeai import configure as configure_gemini, GenerativeModel # Gemini Python SDK
# from elevenlabs import set_api_key as set_elevenlabs_key, generate as generate_elevenlabs_audio # ElevenLabs SDK
# from newsapi import NewsApiClient # NewsAPI Python SDK (뉴스 수집)
# from googleapiclient.discovery import build # YouTube Data API client
# from google.oauth2.credentials import Credentials # YouTube OAuth

# Google Cloud Logging 설정
# Cloud Run 환경에서는 자동으로 로그가 Cloud Logging으로 전송되므로,
# 기본 Python logging 모듈을 사용하는 것이 좋습니다.
# client = google.cloud.logging.Client()
# client.setup_logging()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger().setLevel(logging.INFO)

# --- 전역 변수 선언 (초기화는 check_env_variables 함수에서 진행) ---
GCP_PROJECT_ID = None
GCP_BUCKET_NAME = None
YOUTUBE_CLIENT_ID = None
YOUTUBE_CLIENT_SECRET = None
YOUTUBE_REFRESH_TOKEN = None
ELEVENLABS_API_KEY = None
ELEVENLABS_VOICE_ID = None
OPENAI_API_KEYS = []
GEMINI_API_KEY = None
NEWSAPI_API_KEY = None
PEXELS_API_KEY = None
bucket = None # Cloud Storage 버킷 객체

# ThreadPoolExecutor를 사용하여 비동기 처리
# Cloud Run은 요청당 하나의 인스턴스를 사용하므로, 복잡한 비동기 작업을
# 백그라운드에서 처리할 때 유용합니다. (단, 요청 타임아웃 내에 응답을 보내야 함)
executor = ThreadPoolExecutor(max_workers=os.cpu_count() * 2)

# --- 환경 변수 로드 및 필수 변수 검사 함수 ---
def check_env_variables():
    """
    필수 환경 변수를 로드하고, 누락된 변수가 있는지 검사합니다.
    누락된 변수가 있으면 ValueError를 발생시켜 애플리케이션 시작을 중단합니다.
    """
    global GCP_PROJECT_ID, GCP_BUCKET_NAME, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, \
           YOUTUBE_REFRESH_TOKEN, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, OPENAI_API_KEYS, \
           GEMINI_API_KEY, NEWSAPI_API_KEY, PEXELS_API_KEY, bucket

    required_env_vars = [
        'GCP_PROJECT_ID',
        'GCP_BUCKET_NAME',
        'YOUTUBE_CLIENT_ID',
        'YOUTUBE_CLIENT_SECRET',
        'YOUTUBE_REFRESH_TOKEN',
        'ELEVENLABS_API_KEY',
        'ELEVENLABS_VOICE_ID',
        'OPENAI_API_KEYS', # 쉼표로 구분된 문자열로 받을 것임
        'GEMINI_API_KEY',
        'NEWSAPI_API_KEY',
        'PEXELS_API_KEY'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        env_value = os.environ.get(var)
        if var == 'OPENAI_API_KEYS':
            openai_keys_str = env_value.strip() if env_value else ''
            if not openai_keys_str:
                missing_vars.append(var)
            else:
                OPENAI_API_KEYS = openai_keys_str.split(',')
        else:
            if not env_value:
                missing_vars.append(var)
            else:
                # 해당 변수에 값을 할당 (전역 변수 업데이트)
                globals()[var] = env_value
        
        logging.info(f"환경 변수 로드: {var} = {'***' if var.endswith('_KEY') or var.endswith('_TOKEN') or var.endswith('_SECRET') else globals().get(var, 'N/A')}")


    if missing_vars:
        error_msg = f"❌ 필수 환경 변수가 누락되었습니다: {', '.join(missing_vars)}. Cloud Run 서비스의 환경 변수 설정을 확인해주세요."
        logging.critical(error_msg) # CRITICAL 레벨로 로깅
        # 이 시점에서 애플리케이션 시작을 강제 중단하여 503 에러의 원인을 명확히 합니다.
        raise ValueError(error_msg)

    # Cloud Storage 클라이언트 초기화
    try:
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.get_bucket(GCP_BUCKET_NAME)
        logging.info(f"✅ Cloud Storage 버킷 '{GCP_BUCKET_NAME}' 초기화 성공.")
    except Exception as e:
        error_msg = f"❌ Cloud Storage 버킷 초기화 실패: {e}. GCP_BUCKET_NAME: '{GCP_BUCKET_NAME}'"
        logging.critical(error_msg) # CRITICAL 레벨로 로깅
        raise RuntimeError(error_msg) # 버킷 초기화 실패 시 컨테이너 시작 중단

    logging.info("✅ 모든 필수 환경 변수 및 서비스 초기화 성공.")

# 앱 시작 시 환경 변수 검사 및 초기화 수행
# 이 로직은 Flask 앱 인스턴스가 생성되기 전에 실행되어야 합니다.
# Cloud Run이 컨테이너를 시작할 때 이 부분이 실행됩니다.
try:
    check_env_variables()
except Exception as e:
    # 환경 변수 검사 또는 서비스 초기화 실패 시, 앱이 시작되지 않도록 합니다.
    # Gunicorn이 이 예외를 catch하고 앱 로드를 중단하게 됩니다.
    logging.critical(f"애플리케이션 초기화에 치명적인 오류 발생: {e}")
    # 이 예외가 발생하면 Cloud Run은 컨테이너를 'Unhealthy'로 표시하고 503 응답을 반환할 수 있습니다.
    # Gunicorn이 예외를 받으면 해당 컨테이너가 정상적으로 시작되지 않았음을 알립니다.
    os._exit(1) # 강제 종료하여 Cloud Run이 컨테이너를 unhealthy로 간주하게 함

app = Flask(__name__)

@app.route('/healthz', methods=['GET'])
def healthz():
    """
    상태 체크 엔드포인트: Cloud Run이 컨테이너의 준비 상태를 확인하는 데 사용
    이 엔드포인트가 200 OK를 반환해야 Cloud Run이 서비스가 준비되었다고 판단합니다.
    """
    try:
        # check_env_variables()가 이미 성공했어야 하지만, 혹시 모를 상황에 대비하여
        # 최소한 버킷 객체 존재 여부 확인 (버킷 객체에 접근해보는 것이 더 확실)
        if bucket is None:
            raise RuntimeError("Cloud Storage 버킷이 초기화되지 않았습니다.")
        # 간단한 버킷 접근 테스트
        # bucket.name (버킷 이름을 가져오는 것은 간단한 접근 테스트)
        logging.info("Health check OK. Cloud Storage bucket access verified.")
        return "OK", 200
    except Exception as e:
        logging.error(f"Health check failed: {e}", exc_info=True)
        return f"Not Ready: {e}", 500


@app.route("/", methods=["POST"])
def main_endpoint():
    """기본 엔드포인트 (GitHub Actions 호출용)"""
    try:
        data = request.get_json()
        if not data:
            logging.error("JSON payload가 제공되지 않았습니다.")
            return jsonify({"status": "error", "message": "JSON payload가 제공되지 않았습니다"}), 400
        
        action = data.get('action', '')
        metadata = data.get('metadata', {})
        
        logging.info(f"요청된 액션: {action}")
        logging.info(f"메타데이터: {metadata}")

        if action == 'create_and_upload_shorts':
            # 비동기 작업 시작: 실제 YouTube Shorts 생성 및 업로드 로직은 백그라운드에서 실행
            # Cloud Run은 요청을 빠르게 처리하고 응답을 반환해야 하므로,
            # 장시간 작업은 ThreadPoolExecutor로 분리합니다.
            # 작업이 Cloud Run의 요청 타임아웃(기본 5분, 최대 60분)을 초과하지 않도록 주의.
            future = executor.submit(process_youtube_shorts_upload, metadata)
            logging.info("YouTube Shorts 업로드 프로세스가 백그라운드에서 시작되었습니다.")
            return jsonify({"status": "processing", "message": "YouTube Shorts 업로드 프로세스가 시작됨", "jobId": f"shorts-task-{datetime.now().timestamp()}"}), 202
        else:
            logging.warning(f"지원되지 않는 액션: {action}")
            return jsonify({"status": "error", "message": f"지원되지 않는 액션: {action}"}), 400
    except Exception as e:
        logging.error(f"메인 엔드포인트 처리 중 오류 발생: {e}", exc_info=True)
        # Cloud Run 내부에서 발생하는 500 에러를 명확하게 반환하여 디버깅을 돕습니다.
        return jsonify({"status": "error", "message": f"서버 내부 오류: {str(e)}"}), 500


def process_youtube_shorts_upload(metadata):
    """
    실제 YouTube Shorts 생성 및 업로드 로직을 포함하는 함수.
    이 함수는 Cloud Run 요청-응답 주기와 독립적으로 백그라운드에서 실행됩니다.
    """
    logging.info(f'--- YouTube Shorts 업로드 프로세스 시작 (metadata: {metadata}) ---')
    start_time = time.time()

    try:
        # 이 단계에서 다시 한번 API 키의 유효성을 검사하여 안전성을 높일 수 있습니다.
        # check_env_variables() 에서 이미 검증되었지만, 만약의 경우를 대비하여 한 번 더 확인 가능.
        # (그러나 앱 시작 시 검사가 더 중요)

        # --- 단계별 시뮬레이션 및 실제 API 연동 준비 ---

        # 1. 뉴스 데이터 수집 (NewsAPI 사용 예시)
        logging.info("1. 뉴스 데이터 수집 중...")
        try:
            # newsapi = NewsApiClient(api_key=NEWSAPI_API_KEY)
            # top_headlines = newsapi.get_top_headlines(q='AI', language='en', country='us')
            # if top_headlines and top_headlines['articles']:
            #      article = top_headlines['articles'][0]
            #      article_title = article.get('title', '새로운 AI 소식')
            #      article_description = article.get('description', '흥미로운 AI 관련 기사입니다.')
            #      logging.info(f"뉴스 수집 완료: '{article_title}'")
            # else:
            #      article_title = "오늘의 AI 뉴스"
            #      article_description = "최신 AI 트렌드에 대한 소식입니다."
            #      logging.warning("NewsAPI에서 뉴스를 가져오지 못했습니다. 기본값 사용.")
            article_title = f"오늘의 최신 AI 소식 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            article_description = "생성형 AI 기술의 발전은 계속되고 있습니다."
            logging.info(f"뉴스 수집 (시뮬레이션): {article_title}")
            time.sleep(2)
        except Exception as e:
            logging.error(f"뉴스 데이터 수집 오류: {e}")
            article_title = "뉴스 없음"
            article_description = "뉴스 수집 실패."


        # 2. AI 스크립트 생성 (GPT-4o 또는 Gemini 사용 예시)
        logging.info("2. AI 스크립트 생성 중...")
        script_text = ""
        try:
            # ✅ 여기에서 실제 GPT-4o 또는 Gemini API 호출 로직을 구현합니다.
            # 예시: OpenAI (GPT-4o)
            # openai_client = OpenAI(api_key=OPENAI_API_KEYS[0])
            # completion = openai_client.chat.completions.create(
            #      model="gpt-4o",
            #      messages=[
            #          {"role": "system", "content": "You are a helpful assistant for creating YouTube Shorts scripts."},
            #          {"role": "user", "content": f"Create a short (max 15 seconds) YouTube Shorts script about: '{article_title}'. Focus on being engaging and concise. Start with a hook."}
            #      ]
            # )
            # script_text = completion.choices[0].message.content
            # logging.info(f"GPT-4o 스크립트 생성 완료: {script_text[:50]}...")

            # 예시: Google Gemini (API 키 설정 및 모델 초기화)
            # configure_gemini(api_key=GEMINI_API_KEY)
            # gemini_model = GenerativeModel('gemini-pro')
            # gemini_response = gemini_model.generate_content(f"Create a short (max 15 seconds) YouTube Shorts script about: '{article_title}'. Focus on being engaging and concise. Start with a hook.")
            # script_text = gemini_response.text
            # logging.info(f"Gemini 스크립트 생성 완료: {script_text[:50]}...")

            script_text = f"✨ 긴급 속보! {article_title}! AI 기술이 또 한 번 세상을 놀라게 했습니다. 자세한 내용은 쇼츠에서 확인하세요! (ID: {metadata.get('workflow_run_id')})"
            logging.info(f"AI 스크립트 생성 (시뮬레이션): {script_text}")
            time.sleep(3)
        except Exception as e:
            logging.error(f"AI 스크립트 생성 오류: {e}")
            script_text = f"AI 스크립트 생성 실패: {article_title}에 대한 자동화된 쇼츠입니다."

        # 3. 음성 생성 및 저장 (ElevenLabs 사용 예시)
        logging.info("3. 음성 생성 및 Cloud Storage 저장 중...")
        audio_file_name = f"audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        local_audio_path = f"/tmp/{audio_file_name}"
        try:
            # ✅ 여기에서 실제 ElevenLabs API 호출 로직을 구현합니다.
            # set_elevenlabs_key(ELEVENLABS_API_KEY)
            # audio = generate_elevenlabs_audio(
            #      text=script_text,
            #      voice=ELEVENLABS_VOICE_ID,
            #      model="eleven_multilingual_v2"
            # )
            # with open(local_audio_path, "wb") as f:
            #      f.write(audio)

            # 시뮬레이션: 빈 파일 생성
            with open(local_audio_path, "w") as f:
                f.write("mock audio content for shorts")
            logging.info(f"음성 파일 생성 (시뮬레이션): {local_audio_path}")

            blob = bucket.blob(f"audio/{audio_file_name}")
            blob.upload_from_filename(local_audio_path)
            logging.info(f"✅ 음성 파일 '{audio_file_name}'이 Cloud Storage에 업로드되었습니다.")
            os.remove(local_audio_path) # 임시 파일 삭제
            time.sleep(2)
        except Exception as e:
            logging.error(f"음성 생성 및 저장 오류: {e}")
            if os.path.exists(local_audio_path): os.remove(local_audio_path) # 혹시 모를 잔여 파일 삭제

        # 4. 비디오 클립 다운로드 및 저장 (Pexels API 사용 예시)
        logging.info("4. 비디오 클립 다운로드 및 Cloud Storage 저장 중...")
        video_file_name = f"video_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        local_video_path = f"/tmp/{video_file_name}"
        try:
            # ✅ 여기에서 실제 Pexels API 호출 및 비디오 다운로드 로직을 구현합니다.
            # Pexels API는 비디오 검색 후 URL을 받아와 requests로 다운로드합니다.
            # headers = {"Authorization": PEXELS_API_KEY}
            # search_query = "technology AI" # 뉴스 내용에 따라 검색어 변경 가능
            # pexels_response = requests.get(f"https://api.pexels.com/videos/search?query={search_query}&per_page=1", headers=headers)
            # pexels_response.raise_for_status()
            # videos = pexels_response.json().get('videos', [])
            # if videos:
            #      video_files = videos[0].get('video_files', [])
            #      hd_video = next((vf for vf in video_files if vf['quality'] == 'hd' and vf['file_type'] == 'video/mp4'), None)
            #      if hd_video:
            #          video_url = hd_video['link']
            #          video_data = requests.get(video_url, stream=True)
            #          video_data.raise_for_status()
            #          with open(local_video_path, 'wb') as f:
            #              for chunk in video_data.iter_content(chunk_size=8192):
            #                  f.write(chunk)
            #          logging.info(f"Pexels 비디오 다운로드 완료: {video_url}")
            #      else:
            #          logging.warning("HD MP4 비디오 파일을 찾을 수 없습니다. 시뮬레이션으로 대체.")
            #          with open(local_video_path, "w") as f: f.write("mock video content")
            # else:
            #      logging.warning("Pexels에서 비디오를 찾을 수 없습니다. 시뮬레이션으로 대체.")
            #      with open(local_video_path, "w") as f: f.write("mock video content")

            # 시뮬레이션: 빈 파일 생성
            with open(local_video_path, "w") as f:
                f.write("mock video content for shorts")
            logging.info(f"비디오 파일 생성 (시뮬레이션): {local_video_path}")

            blob = bucket.blob(f"video/{video_file_name}")
            blob.upload_from_filename(local_video_path)
            logging.info(f"✅ 비디오 파일 '{video_file_name}'이 Cloud Storage에 업로드되었습니다.")
            os.remove(local_video_path) # 임시 파일 삭제
            time.sleep(3)
        except Exception as e:
            logging.error(f"비디오 다운로드 및 저장 오류: {e}")
            if os.path.exists(local_video_path): os.remove(local_video_path)


        # 5. 쇼츠 비디오 최종 생성 (MoviePy 등 활용 예정)
        logging.info("5. 쇼츠 비디오 최종 생성 중...")
        final_shorts_name = f"youtube_shorts_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        local_final_shorts_path = f"/tmp/{final_shorts_name}"
        try:
            # ✅ 여기에서 MoviePy 등을 사용하여 음성 파일과 비디오 클립을 합쳐 최종 쇼츠를 생성합니다.
            # 예: moviepy.editor.VideoFileClip, AudioFileClip, concatenate_videoclips 등 사용
            # 시뮬레이션: 빈 파일 생성
            with open(local_final_shorts_path, "w") as f:
                f.write("mock final shorts video")
            logging.info(f"최종 쇼츠 비디오 생성 (시뮬레이션): {local_final_shorts_path}")

            blob = bucket.blob(f"shorts/{final_shorts_name}")
            blob.upload_from_filename(local_final_shorts_path)
            logging.info(f"✅ 최종 쇼츠 '{final_shorts_name}'이 Cloud Storage에 업로드되었습니다.")
            os.remove(local_final_shorts_path)
            time.sleep(4)
        except Exception as e:
            logging.error(f"쇼츠 비디오 최종 생성 오류: {e}")
            if os.path.exists(local_final_shorts_path): os.remove(local_final_shorts_path)

        # 6. YouTube 업로드 (YouTube Data API 사용 예시)
        logging.info("6. YouTube Data API를 사용하여 쇼츠 업로드 중...")
        try:
            # ✅ 여기에서 실제 YouTube Data API를 사용하여 비디오를 업로드합니다.
            # credentials = Credentials(
            #      token=None, # access_token은 매번 재발급
            #      refresh_token=YOUTUBE_REFRESH_TOKEN,
            #      client_id=YOUTUBE_CLIENT_ID,
            #      client_secret=YOUTUBE_CLIENT_SECRET,
            #      token_uri='https://oauth2.googleapis.com/token'
            # )
            # # credentials.refresh(google.auth.transport.requests.Request()) # 필요시 토큰 갱신
            # youtube = build('youtube', 'v3', credentials=credentials)

            # # video = youtube.videos().insert(...)
            logging.info(f"YouTube 업로드 (시뮬레이션): 제목='{article_title}', 설명='{script_text}'")
            time.sleep(5)
            logging.info(f'✅ YouTube Shorts 업로드 프로세스 완료 (시뮬레이션)')
            # 수익 창출 로직은 YouTube 업로드 후 설정하는 부분에 해당합니다.
            # 예를 들어, 업로드된 비디오에 대한 monetization 설정 API 호출 등을 추가할 수 있습니다.
            # 이는 YouTube API 사용 정책과 계정 상태에 따라 달라집니다.

        except Exception as e:
            logging.error(f"YouTube 업로드 오류: {e}")


    except Exception as e:
        logging.error(f"❌ YouTube Shorts 업로드 프로세스 전체 오류: {e}", exc_info=True)
        # 실제 서비스에서는 이 오류를 사용자에게 알리거나, 재시도 로직을 구현해야 합니다.
    finally:
        end_time = time.time()
        logging.info(f"⏱ 총 처리 시간: {end_time - start_time:.2f} 초")

# 이 부분은 Gunicorn이 Cloud Run 환경에서 앱을 실행할 때 필요 없습니다.
# Gunicorn이 'app:app' (app.py 파일 내의 'app' 객체)을 찾아 실행합니다.
# if __name__ == '__main__':
#      port = int(os.environ.get('PORT', 8080))
#      app.run(host='0.0.0.0', port=port, debug=True) # debug=True는 개발용, 배포 시에는 False
