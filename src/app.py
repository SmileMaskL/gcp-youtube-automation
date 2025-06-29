# cloud_run_service/main.py

import os
import datetime
import logging
from flask import Flask, request, jsonify
from google.cloud import storage
import google.cloud.texttospeech as tts
from google.cloud import youtube_v3
import google.generativeai as genai # Google Gemini Pro 사용 예시
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, ImageClip, concatenate_videoclips
import random
import string
import shutil
import time

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# 환경 변수 설정
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY') # YouTube Data API v3 키
GOOGLE_CLOUD_PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT_ID') # GCP 프로젝트 ID

# Cloud Storage 클라이언트 초기화 (서비스 계정 권한으로 자동 인증)
storage_client = storage.Client(project=GOOGLE_CLOUD_PROJECT_ID)
BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'your-youtube-shorts-bucket') # 본인의 GCS 버킷 이름으로 변경 필요!
output_bucket = storage_client.bucket(BUCKET_NAME)

# Google Text-to-Speech 클라이언트 초기화
tts_client = tts.TextToSpeechClient()

# Google Gemini Pro 설정 (무료 티어 활용 가능성 높음)
# 서비스 계정으로 인증되므로 API 키는 필요 없음. Vertex AI API 활성화 필수.
# from vertexai.preview.generative_models import GenerativeModel
# model = GenerativeModel("gemini-pro") 

@app.route('/', methods=['POST'])
def handle_request():
    try:
        data = request.get_json()
        logging.info(f"Received request: {data}")

        action = data.get('action')
        metadata = data.get('metadata', {})
        workflow_run_id = metadata.get('workflow_run_id', 'manual_run')
        news_topic = metadata.get('news_topic', '최신 기술 트렌드') # 기본값

        if action == "create_and_upload_shorts":
            # 1. AI로 뉴스 스크립트 생성 (Google Gemini Pro 활용 예시)
            logging.info(f"Generating news script for topic: {news_topic} using Google Gemini Pro...")
            script = generate_ai_script(news_topic)
            logging.info(f"Generated script: {script[:100]}...") # 처음 100자만 출력

            # 2. 스크립트를 음성 파일로 변환 (Google Text-to-Speech)
            logging.info("Converting script to audio...")
            audio_path = text_to_speech(script, workflow_run_id)
            logging.info(f"Audio saved to: {audio_path}")

            # 3. 비디오 생성 (간단한 배경 이미지 + 음성)
            logging.info("Creating video...")
            video_path = create_video(audio_path, workflow_run_id)
            logging.info(f"Video saved to: {video_path}")

            # 4. YouTube Shorts에 업로드
            logging.info("Uploading video to YouTube Shorts...")
            youtube_video_id = upload_to_youtube(video_path, script, news_topic)
            logging.info(f"Video uploaded to YouTube with ID: {youtube_video_id}")

            # 5. 로컬 파일 정리 (Cloud Run 컨테이너에서 임시 파일 삭제)
            clean_up_local_files(audio_path, video_path)

            return jsonify({
                "status": "success",
                "message": "YouTube Shorts created and uploaded successfully!",
                "workflow_run_id": workflow_run_id,
                "youtube_video_id": youtube_video_id,
                "video_url": f"https://www.youtube.com/shorts/{youtube_video_id}"
            }), 200

        else:
            return jsonify({"status": "error", "message": "Invalid action specified."}), 400

    except Exception as e:
        logging.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

# --- 핵심 기능 구현 ---

# 1. AI로 뉴스 스크립트 생성 함수 (Gemini Pro 사용 예시)
def generate_ai_script(topic):
    try:
        # 이 부분에서 실제 Gemini Pro API를 호출합니다.
        # Vertex AI SDK를 사용하려면, Cloud Run 서비스 계정에 'Vertex AI 사용자' 권한이 필요합니다.
        # 코드 배포 전에 'vertexai' 라이브러리를 requirements.txt에 추가해야 합니다.
        """
        # from vertexai.preview.generative_models import GenerativeModel
        # model = GenerativeModel("gemini-pro") 
        # response = model.generate_content(
        #     f"'{topic}'에 대한 흥미롭고 짧은(500자 이내) YouTube Shorts 스크립트를 작성해줘. "
        #     "최신 정보를 바탕으로 호기심을 자극하고 간결하게 작성하며, 마지막에 궁금증을 남기는 형식으로 해줘. "
        #     "예시: '놀라운 신기술이 등장했습니다! 우리 삶을 어떻게 바꿀까요? 다음 쇼츠에서 더 알아봐요!'"
        # )
        # return response.text
        """
        # 현재는 예시 응답을 반환합니다. 실제 AI 통합 시 위 주석 처리된 코드를 활성화하세요.
        prompt = (
            f"'{topic}'에 대한 흥미롭고 짧은(500자 이내) YouTube Shorts 스크립트를 작성해줘. "
            "최신 정보를 바탕으로 호기심을 자극하고 간결하게 작성하며, 마지막에 궁금증을 남기는 형식으로 해줘. "
            "예시: '놀라운 신기술이 등장했습니다! 우리 삶을 어떻게 바꿀까요? 다음 쇼츠에서 더 알아봐요!'"
        )
        # Google Gemini API 호출 (로컬 테스트용 또는 API 키 설정 시)
        # genai.configure(api_key="YOUR_GEMINI_API_KEY") # API 키를 사용하는 경우 (클라우드 환경에서는 서비스 계정 인증)
        # gemini_model = genai.GenerativeModel('gemini-pro')
        # response = gemini_model.generate_content(prompt)
        # return response.text

        # 실제 AI API 연동 전 테스트를 위해 임시 스크립트 반환
        return (
            f"오늘의 최신 과학 기술 뉴스는 '{topic}'입니다. 놀라운 발견이 우리의 미래를 바꿀 준비를 하고 있어요! "
            "과연 어떤 혁신이 우리를 기다리고 있을까요? 다음 쇼츠에서 더 자세히 알아봐요! "
            "놓치지 마세요! 이 기술이 당신의 삶을 어떻게 변화시킬지 궁금하지 않나요?"
        )
    except Exception as e:
        logging.error(f"Error generating AI script: {e}")
        # 오류 발생 시 기본 스크립트 반환
        return f"오늘의 최신 뉴스: {topic}. 놀라운 소식들이 가득합니다! 다음 쇼츠에서 더 자세히 알아볼까요?"

# 2. 텍스트를 음성으로 변환하는 함수
def text_to_speech(text, file_id):
    synthesis_input = tts.SynthesisInput(text=text)
    # 한국어 여성 목소리 선택 (다른 목소리를 원하면 변경 가능)
    voice = tts.VoiceSelectionParams(language_code="ko-KR", name="ko-KR-Wavenet-A", ssml_gender=tts.SsmlVoiceGender.FEMALE)
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.MP3)

    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    audio_file_name = f"shorts_audio_{file_id}.mp3"
    audio_file_path = os.path.join("/tmp", audio_file_name) # Cloud Run 임시 디렉토리
    with open(audio_file_path, "wb") as out:
        out.write(response.audio_content)
    return audio_file_path

# 3. 비디오 생성 함수
def create_video(audio_path, file_id):
    # 빈 배경 비디오 또는 단색 이미지 사용 (간단화를 위해)
    # 실제 프로젝트에서는 더 풍부한 배경 비디오나 이미지 시퀀스 사용 가능
    # 임시 이미지 파일 생성
    background_image_path = "/tmp/background.png"
    # 간단한 단색 이미지 생성 (MoviePy에 이미지 로드 후 크기 조정)
    # MoviePy ImageClip은 Pillow를 필요로 함 (requirements.txt에 Pillow 추가)
    from PIL import Image
    Image.new('RGB', (1080, 1920), color = 'black').save(background_image_path) # 쇼츠 비율 (9:16)

    audio_clip = AudioFileClip(audio_path)
    video_duration = audio_clip.duration + 1 # 음성 길이에 1초 추가 여유

    # 쇼츠에 적합한 9:16 비율 (1080x1920)로 비디오 생성
    video_clip = ImageClip(background_image_path, duration=video_duration)
    video_clip = video_clip.set_fps(24) # 프레임 속도 설정

    final_clip = video_clip.set_audio(audio_clip)

    video_file_name = f"youtube_shorts_{file_id}.mp4"
    video_file_path = os.path.join("/tmp", video_file_name) # Cloud Run 임시 디렉토리
    
    # 코덱 설정: libx264 (H.264)는 유튜브에 적합하며, crf=23은 품질과 파일 크기의 균형을 맞춥니다.
    # preset=medium은 인코딩 속도와 품질의 균형을 맞춥니다.
    final_clip.write_videofile(
        video_file_path,
        codec='libx264',
        audio_codec='aac',
        fps=24,
        preset='medium',
        ffmpeg_params=["-crf", "23"]
    )
    return video_file_path


# 4. YouTube Shorts에 업로드하는 함수
def upload_to_youtube(video_path, description, topic):
    youtube = youtube_v3.resource_with_developer_key(YOUTUBE_API_KEY)

    # 비디오 메타데이터 설정
    # 쇼츠로 인식되도록 제목 또는 설명에 #Shorts 포함
    title = f"오늘의 최신 뉴스: {topic} #Shorts #AI #기술"
    description_full = f"{description}\n\n#인공지능 #최신기술 #과학 #놀라운발견"
    keywords = ["AI", "인공지능", "과학기술", "최신뉴스", "쇼츠", "자동화"]
    
    body = {
        'snippet': {
            'title': title,
            'description': description_full,
            'tags': keywords,
            'categoryId': '28' # 과학 기술 카테고리 (필요에 따라 변경)
        },
        'status': {
            'privacyStatus': 'public' # 'public', 'private', 'unlisted' 중 선택
        }
    }

    # 파일 업로드
    media_body = youtube_v3.MediaFileUpload(
        video_path, mimetype='video/mp4', chunksize=-1, resumable=True
    )

    # API 요청 실행
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media_body
    )

    response = request.execute()
    return response['id']

# 5. 로컬 임시 파일 정리
def clean_up_local_files(*file_paths):
    for path in file_paths:
        if os.path.exists(path):
            os.remove(path)
            logging.info(f"Cleaned up local file: {path}")
    # /tmp 디렉토리 자체가 비워지도록 추가 (MoviePy 등 다른 라이브러리 임시 파일)
    for item in os.listdir('/tmp'):
        item_path = os.path.join('/tmp', item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        except Exception as e:
            logging.warning(f'Failed to delete {item_path}. Reason: {e}')


# Cloud Run 실행 환경 설정
if __name__ == '__main__':
    # Cloud Run은 PORT 환경 변수를 통해 포트를 지정합니다.
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
