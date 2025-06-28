# src/main.py
import os
import json
import logging
import itertools # 키 로테이션을 위한 모듈 추가
from flask import Flask, request, jsonify

# 필요한 모듈 임포트
from .content_generator import generate_content_and_script
from .tts_generator import generate_tts_audio
from .video_creator import create_youtube_video
from .youtube_uploader import YouTubeUploader # YouTubeUploader 클래스 임포트
from .utils import cleanup_local_files # 임시 파일 정리를 위한 유틸리티 함수

app = Flask(__name__)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 전역 변수로 OpenAI API 키 목록과 이터레이터를 초기화합니다.
# 이들은 애플리케이션 시작 시 한 번만 로드됩니다.
OPENAI_API_KEYS = []
api_key_iterator = None

# 애플리케이션 컨텍스트 외부에서 환경 변수를 미리 로드합니다.
# Flask 앱이 로드될 때 한 번 실행됩니다.
def load_openai_keys():
    global OPENAI_API_KEYS, api_key_iterator
    openai_api_keys_str = os.environ.get('OPENAI_API_KEYS')
    # GitHub Secrets에 저장할 때 사용한 구분자(세미콜론 ';')로 분리합니다.
    OPENAI_API_KEYS = [key.strip() for key in openai_api_keys_str.split(';') if key.strip()] if openai_api_keys_str else []
    
    if not OPENAI_API_KEYS:
        logging.warning("OPENAI_API_KEYS 환경 변수가 설정되지 않았거나 비어 있습니다.")
    else:
        api_key_iterator = itertools.cycle(OPENAI_API_KEYS)
        logging.info(f"Loaded {len(OPENAI_API_KEYS)} OpenAI API keys.")

load_openai_keys() # 앱 시작 시 키 로드

def get_next_openai_key():
    """
    로테이션 방식으로 다음 OpenAI API 키를 반환합니다.
    """
    if not api_key_iterator:
        # 키가 로드되지 않았거나 비어 있는 경우
        logging.error("OpenAI API 키 이터레이터가 초기화되지 않았습니다.")
        raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
    
    return next(api_key_iterator)


@app.route('/', methods=['POST'])
def handle_request():
    """
    Cloud Run 서비스의 HTTP 트리거 진입점.
    요청을 받아 콘텐츠 생성 및 업로드 워크플로우를 시작합니다.
    """
    try:
        request_json = request.get_json(silent=True)
        action = request_json.get('action', 'create_and_upload_shorts') # 기본 액션 설정

        logging.info(f"Received action: {action}")

        # 모든 필요한 환경 변수 로드
        project_id = os.environ.get('GCP_PROJECT_ID')
        bucket_name = os.environ.get('GCP_BUCKET_NAME')
        elevenlabs_api_key = os.environ.get('ELEVENLABS_API_KEY')
        elevenlabs_voice_id = os.environ.get('ELEVENLABS_VOICE_ID')
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        news_api_key = os.environ.get('NEWS_API_KEY')
        pexels_api_key = os.environ.get('PEXELS_API_KEY')
        youtube_client_id = os.environ.get('YOUTUBE_CLIENT_ID')
        youtube_client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
        youtube_refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')
        
        # 필수 환경 변수 누락 확인
        required_env_vars = {
            'GCP_PROJECT_ID': project_id,
            'ELEVENLABS_API_KEY': elevenlabs_api_key,
            'ELEVENLABS_VOICE_ID': elevenlabs_voice_id,
            'GEMINI_API_KEY': gemini_api_key,
            'NEWS_API_KEY': news_api_key,
            'PEXELS_API_KEY': pexels_api_key,
            'YOUTUBE_CLIENT_ID': youtube_client_id,
            'YOUTUBE_CLIENT_SECRET': youtube_client_secret,
            'YOUTUBE_REFRESH_TOKEN': youtube_refresh_token
        }
        
        missing_vars = [name for name, value in required_env_vars.items() if not value]
        if not OPENAI_API_KEYS: # OpenAI API 키도 필수 확인
            missing_vars.append('OPENAI_API_KEYS')

        if missing_vars:
            error_msg = f"Missing one or more required environment variables: {', '.join(missing_vars)}"
            logging.error(error_msg)
            return jsonify({'error': error_msg}), 500

        # 임시 파일 경로를 저장할 리스트
        temp_files_to_clean = []

        if action == 'create_and_upload_shorts':
            logging.info("Starting YouTube Shorts content generation and upload process...")
            
            # 1. 콘텐츠 및 스크립트 생성 (Gemini 및 News API 활용)
            # OpenAI API 키는 로테이션 방식으로 하나씩 전달합니다.
            current_openai_key = get_next_openai_key() 
            content_data = generate_content_and_script(gemini_api_key, news_api_key, current_openai_key) # << 단일 키 전달
            
            title = content_data.get('title', "AI Generated Shorts")
            description = content_data.get('description', "Daily AI generated shorts content.")
            script = content_data.get('script', "Hello, welcome to AI Shorts.")
            keywords = content_data.get('keywords', ["AI Shorts", "Daily Update"])

            # 2. TTS 오디오 생성 (ElevenLabs API 활용)
            audio_file_path = generate_tts_audio(script, elevenlabs_api_key, elevenlabs_voice_id)
            if audio_file_path:
                temp_files_to_clean.append(audio_file_path)

            # 3. 비디오 생성 (Pexels API 및 기타 유틸리티 활용)
            video_file_path = create_youtube_video(
                pexels_api_key, 
                audio_file_path, 
                keywords # 비디오 생성에 키워드가 필요하다면 전달
            )
            
            if not video_file_path or not os.path.exists(video_file_path):
                logging.error("Video creation failed or video file does not exist.")
                return jsonify({'error': 'Video creation failed'}), 500
            temp_files_to_clean.append(video_file_path)

            # 4. YouTube에 비디오 업로드
            uploader = YouTubeUploader(youtube_client_id, youtube_client_secret, youtube_refresh_token)
            uploaded_video_id = uploader.upload_video(
                video_file_path,
                title,
                description,
                keywords,
                privacy_status="private" # 처음에는 비공개로 업로드하여 검토 권장
            )
            
            if uploaded_video_id:
                logging.info(f"Video uploaded successfully! ID: {uploaded_video_id}")
                return jsonify({
                    'status': 'success',
                    'message': 'YouTube Shorts content created and uploaded!',
                    'video_id': uploaded_video_id,
                    'video_url': f"https://www.youtube.com/watch?v={uploaded_video_id}"
                }), 200
            else:
                logging.error("Failed to upload video to YouTube.")
                return jsonify({'error': 'Failed to upload video to YouTube'}), 500

        elif action == 'test_run':
            logging.info("Test run initiated. All environment variables loaded.")
            # 테스트 시 현재 로드된 OpenAI 키 개수도 확인할 수 있습니다.
            return jsonify({'status': 'success', 'message': 'Cloud Run service is reachable and environment variables loaded for test.', 'openai_keys_loaded': len(OPENAI_API_KEYS)}), 200

        else:
            logging.warning(f"Unknown action: {action}")
            return jsonify({'error': 'Unknown action specified'}), 400

    except Exception as e:
        logging.error(f"An error occurred during process: {e}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    finally:
        if temp_files_to_clean:
            logging.info(f"Cleaning up {len(temp_files_to_clean)} temporary files...")
            cleanup_local_files(temp_files_to_clean)
        else:
            logging.info("No temporary files to clean up.")

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=PORT, debug=True)
