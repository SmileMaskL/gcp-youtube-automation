# src/main.py
import os
import json
import logging
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

@app.route('/', methods=['POST'])
def handle_request():
    """
    Cloud Run 서비스의 HTTP 트리거 진입점.
    요청을 받아 콘텐츠 생성 및 업로드 워크플로우를 시작합니다.
    """
    try:
        request_json = request.get_json(silent=True)
        # 기본 액션은 'create_and_upload_shorts'로 설정
        action = request_json.get('action', 'create_and_upload_shorts') 

        logging.info(f"Received action: {action}")

        # 모든 필요한 환경 변수 로드
        # Secret Manager에서 직접 가져오는 대신, GitHub Actions에서 Cloud Run으로 환경 변수로 전달됨
        project_id = os.environ.get('GCP_PROJECT_ID')
        bucket_name = os.environ.get('GCP_BUCKET_NAME') # 현재 코드에서는 사용되지 않지만, 필요 시 GCS 활용
        elevenlabs_api_key = os.environ.get('ELEVENLABS_API_KEY')
        elevenlabs_voice_id = os.environ.get('ELEVENLABS_VOICE_ID')
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        news_api_key = os.environ.get('NEWS_API_KEY')
        openai_api_keys_str = os.environ.get('OPENAI_API_KEYS') # 쉼표로 구분된 문자열로 받음
        pexels_api_key = os.environ.get('PEXELS_API_KEY')
        youtube_client_id = os.environ.get('YOUTUBE_CLIENT_ID')
        youtube_client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
        youtube_refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')
        # GCP_PROJECT_NUMBER는 Secret Manager에서 사용될 수 있지만, 현재는 main.py에서 직접 사용하지 않음

        # OpenAI API 키는 여러 개일 수 있으므로 쉼표로 분리하여 리스트로 만듭니다.
        openai_api_keys = [key.strip() for key in openai_api_keys_str.split(',') if key.strip()] if openai_api_keys_str else []
        
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
        if missing_vars:
            error_msg = f"Missing one or more required environment variables: {', '.join(missing_vars)}"
            logging.error(error_msg)
            return jsonify({'error': error_msg}), 500

        # 임시 파일 경로를 저장할 리스트
        temp_files_to_clean = []

        if action == 'create_and_upload_shorts':
            logging.info("Starting YouTube Shorts content generation and upload process...")
            
            # 1. 콘텐츠 및 스크립트 생성 (Gemini 및 News API 활용)
            content_data = generate_content_and_script(gemini_api_key, news_api_key, openai_api_keys)
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
            return jsonify({'status': 'success', 'message': 'Cloud Run service is reachable and environment variables loaded for test.'}), 200

        else:
            logging.warning(f"Unknown action: {action}")
            return jsonify({'error': 'Unknown action specified'}), 400

    except Exception as e:
        logging.error(f"An error occurred during process: {e}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    finally:
        # 항상 임시 파일 정리 (오류 발생 여부와 관계없이)
        if temp_files_to_clean:
            logging.info(f"Cleaning up {len(temp_files_to_clean)} temporary files...")
            cleanup_local_files(temp_files_to_clean)
        else:
            logging.info("No temporary files to clean up.")

if __name__ == '__main__':
    # Cloud Run 환경이 아닌 로컬에서 Flask 앱을 실행할 때 사용
    # Gunicorn을 사용하지 않는 경우 (예: 로컬 개발 환경)
    PORT = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=PORT, debug=True)
