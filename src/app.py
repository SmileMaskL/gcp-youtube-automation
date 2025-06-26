# 수정된 파일: src/app.py

import os
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import logging
import google.cloud.logging
from google.cloud import storage, pubsub_v1
import json
import time

# YouTube API 및 기타 서비스 관련 라이브러리 (placeholder)
# 실제 프로젝트에서는 pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 etc.
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
# from googleapiclient.discovery import build
# from elevenlabs import set_api_key, generate, Voice, VoiceSettings
# from openai import OpenAI
# import requests # For NewsAPI, Pexels API

app = Flask(__name__)

# Google Cloud Logging 설정
client = google.cloud.logging.Client()
client.setup_logging()
logging.basicConfig(level=logging.INFO) # 기본 로깅 레벨 설정

# ThreadPoolExecutor를 사용하여 비동기 처리
executor = ThreadPoolExecutor(max_workers=os.cpu_count() * 2) # 적절한 워커 수 설정

# 환경 변수 로드
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
GCP_BUCKET_NAME = os.environ.get('GCP_BUCKET_NAME')

# YouTube API 키 및 토큰 (Secrets에서 로드)
YOUTUBE_CLIENT_ID = os.environ.get('YOUTUBE_CLIENT_ID')
YOUTUBE_CLIENT_SECRET = os.environ.get('YOUTUBE_CLIENT_SECRET')
YOUTUBE_REFRESH_TOKEN = os.environ.get('YOUTUBE_REFRESH_TOKEN')

# ElevenLabs API 키 및 음성 ID
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')
ELEVENLABS_VOICE_ID = os.environ.get('ELEVENLABS_VOICE_ID')

# OpenAI API 키 (여러 개를 쉼표로 구분)
OPENAI_API_KEYS = os.environ.get('OPENAI_API_KEYS', '').split(',')

# Gemini API 키
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# NewsAPI 키
NEWSAPI_API_KEY = os.environ.get('NEWSAPI_API_KEY')

# Pexels API 키
PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY')

# Cloud Storage 클라이언트 초기화
storage_client = storage.Client()
bucket = storage_client.get_bucket(GCP_BUCKET_NAME)

# Pub/Sub 클라이언트 초기화 (필요시)
# publisher = pubsub_v1.PublisherClient()
# TOPIC_PATH = publisher.topic_path(GCP_PROJECT_ID, 'your-pubsub-topic-name') # 실제 토픽 이름으로 변경

@app.route('/healthz', methods=['GET'])
def healthz():
    """상태 체크 엔드포인트"""
    return "OK", 200

@app.route('/upload-youtube-shorts', methods=['POST'])
def upload_youtube_shorts_trigger():
    """
    Cloud Scheduler 또는 다른 HTTP 트리거에 의해 호출되는 엔드포인트.
    비동기 작업을 시작하고 즉시 응답을 반환합니다.
    """
    logging.info('YouTube Shorts 업로드 프로세스 시작 요청 수신.')

    try:
        # 실제 로직을 비동기로 실행
        future = executor.submit(process_youtube_shorts_upload)
        # 작업이 완료될 때까지 기다리지 않고 즉시 응답
        return jsonify({"status": "processing", "message": "YouTube Shorts 업로드 프로세스가 백그라운드에서 시작되었습니다."}), 202
    except Exception as e:
        logging.error(f"YouTube Shorts 업로드 프로세스 시작 실패: {e}")
        return jsonify({"status": "error", "message": f"업로드 프로세스 시작 중 오류 발생: {e}"}), 500

def process_youtube_shorts_upload():
    """
    실제로 YouTube Shorts를 생성하고 업로드하는 모든 로직을 담는 함수.
    이 함수는 Cloud Run 인스턴스 내에서 비동기적으로 실행됩니다.
    """
    logging.info('YouTube Shorts 업로드 프로세스 시작 (백그라운드).')
    start_time = time.time()

    try:
        # 1. 뉴스 데이터 수집 (NewsAPI)
        # response = requests.get(f"https://newsapi.org/v2/top-headlines?country=kr&apiKey={NEWSAPI_API_KEY}")
        # news_data = response.json()
        # article_title = news_data['articles'][0]['title'] if news_data['articles'] else "오늘의 흥미로운 뉴스"
        logging.info("1. 뉴스 데이터 수집 (placeholder).")
        article_title = "오늘의 흥미로운 뉴스"
        time.sleep(1) # 실제 API 호출 시간 시뮬레이션

        # 2. AI를 사용하여 스크립트 생성 (Gemini 또는 OpenAI)
        # from google.generativeai.client import get_default_retrying_generative_client # Gemini
        # from google.generativeai.types import GenerationConfig # Gemini
        # from google.generativeai.protos import GenerateContentRequest # Gemini
        # client = get_default_retrying_generative_client(api_key=GEMINI_API_KEY)
        # model = client.generative_models.GenerativeModel('gemini-pro')
        # response = model.generate_content(f"'{article_title}'에 대한 1분짜리 유튜브 쇼츠 스크립트를 작성해줘. 내용은 간결하고 흥미롭게.",
        #                                  generation_config=GenerationConfig(temperature=0.7))
        # script_text = response.candidates[0].content.parts[0].text
        logging.info("2. AI 스크립트 생성 (placeholder).")
        script_text = f"여러분, {article_title}! 자세한 내용은 쇼츠를 통해 확인하세요!"
        time.sleep(2) # 실제 AI 처리 시간 시뮬레이션

        # 3. ElevenLabs를 사용하여 음성 생성 및 Cloud Storage에 저장
        # set_api_key(ELEVENLABS_API_KEY)
        # audio = generate(
        #     text=script_text,
        #     voice=Voice(voice_id=ELEVENLABS_VOICE_ID,
        #                 settings=VoiceSettings(stability=0.75, similarity_boost=0.75, style=0.0, use_speaker_boost=True)),
        #     model="eleven_multilingual_v2"
        # )
        # audio_filename = "shorts_audio.mp3"
        # with open(audio_filename, "wb") as f:
        #     f.write(audio)
        # blob = bucket.blob(audio_filename)
        # blob.upload_from_filename(audio_filename)
        # os.remove(audio_filename) # 로컬 파일 삭제
        # logging.info(f"3. 음성 파일 Cloud Storage에 저장됨: {blob.public_url}")
        logging.info("3. 음성 생성 및 Cloud Storage 저장 (placeholder).")
        time.sleep(3) # 실제 음성 생성 및 업로드 시간 시뮬레이션

        # 4. Pexels API를 사용하여 관련 비디오 클립 다운로드 및 Cloud Storage에 저장
        # headers = {"Authorization": PEXELS_API_KEY}
        # pexels_response = requests.get(f"https://api.pexels.com/videos/search?query={article_title}&per_page=1", headers=headers)
        # video_url = pexels_response.json()['videos'][0]['video_files'][0]['link'] if pexels_response.json()['videos'] else None
        # if video_url:
        #     video_content = requests.get(video_url).content
        #     video_filename = "shorts_video.mp4"
        #     with open(video_filename, "wb") as f:
        #         f.write(video_content)
        #     blob = bucket.blob(video_filename)
        #     blob.upload_from_filename(video_filename)
        #     os.remove(video_filename)
        #     logging.info(f"4. 비디오 파일 Cloud Storage에 저장됨: {blob.public_url}")
        logging.info("4. 비디오 클립 다운로드 및 Cloud Storage 저장 (placeholder).")
        time.sleep(4) # 실제 비디오 다운로드 및 업로드 시간 시뮬레이션

        # 5. FFmpeg 또는 비디오 편집 라이브러리 (e.g., MoviePy)를 사용하여 쇼츠 비디오 최종 생성
        # (이 부분은 Cloud Run 환경에서 FFmpeg 설치 및 사용이 복잡할 수 있음. Dockerfile에 포함 필요)
        # 예를 들어: moviepy.editor.VideoFileClip, moviepy.editor.AudioFileClip
        logging.info("5. 쇼츠 비디오 최종 생성 (placeholder).")
        time.sleep(5) # 실제 비디오 편집 시간 시뮬레이션

        # 6. YouTube Data API를 사용하여 쇼츠 업로드
        # from google.oauth2.credentials import Credentials
        # from google.oauth2 import client as google_auth_client
        # credentials_data = {
        #     "token": None,
        #     "refresh_token": YOUTUBE_REFRESH_TOKEN,
        #     "token_uri": "https://oauth2.googleapis.com/token",
        #     "client_id": YOUTUBE_CLIENT_ID,
        #     "client_secret": YOUTUBE_CLIENT_SECRET,
        #     "scopes": ["https://www.googleapis.com/auth/youtube.upload"]
        # }
        # credentials = Credentials.from_authorized_user_info(info=credentials_data)
        # # 리프레시 토큰이 만료되었거나 없을 경우, 흐름을 통해 새로 생성해야 함 (수동 과정)
        # if not credentials or not credentials.valid:
        #     if credentials and credentials.expired and credentials.refresh_token:
        #         credentials.refresh(Request())
        #     else:
        #         logging.error("YouTube API 인증 정보가 유효하지 않습니다. 새로운 리프레시 토큰이 필요합니다.")
        #         raise Exception("YouTube API 인증 실패")

        # youtube = build('youtube', 'v3', credentials=credentials)
        # body = {
        #     'snippet': {
        #         'title': f'AI 생성 쇼츠: {article_title}',
        #         'description': '이 비디오는 AI에 의해 자동으로 생성되었습니다.',
        #         'tags': ['AI', 'YouTubeShorts', '자동생성', '뉴스'],
        #         'categoryId': '22' # 뉴스 및 정치 카테고리
        #     },
        #     'status': {
        #         'privacyStatus': 'public', # 'private', 'unlisted', 'public'
        #         'selfDeclaredMadeForKids': False
        #     },
        #     'videoRecordingDetails': {
        #         'recordingDate': datetime.datetime.now().isoformat() + "Z"
        #     }
        # }
        # insert_request = youtube.videos().insert(
        #     part=','.join(body.keys()),
        #     body=body,
        #     media_body=MediaFileUpload(final_video_filename, chunksize=-1, resumable=True)
        # )
        # response = insert_request.execute()
        # logging.info(f"6. YouTube 쇼츠 업로드 완료: {response.get('id')}")
        logging.info("6. YouTube Data API를 사용하여 쇼츠 업로드 (placeholder).")
        time.sleep(6) # 실제 업로드 시간 시뮬레이션

        logging.info('YouTube Shorts 업로드 프로세스 완료 (현재는 플레이스홀더).')

    except Exception as e:
        logging.error(f"YouTube Shorts 업로드 프로세스 실행 중 오류 발생: {e}", exc_info=True)
        # 오류 발생 시 Pub/Sub 등으로 알림을 보낼 수 있습니다.
        # publisher.publish(TOPIC_PATH, data=json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))

    finally:
        end_time = time.time()
        logging.info(f"총 처리 시간: {end_time - start_time:.2f} 초")

if __name__ == '__main__':
    # Cloud Run은 PORT 환경 변수를 사용합니다.
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False) # Cloud Run 배포 시 debug=False 권장
