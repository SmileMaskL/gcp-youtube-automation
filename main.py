import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from google.cloud import secretmanager
from src.content_generator import ContentGenerator
from src.youtube_uploader import YouTubeUploader
import traceback

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class YouTubeAutomation:
    def __init__(self):
        self.project_id = os.getenv('GCP_PROJECT_ID')
        self.storage_bucket = os.getenv('STORAGE_BUCKET')
        self.content_generator = None
        self.youtube_uploader = None
        self.setup_services()
    
    def get_secret(self, secret_id):
        """Secret Manager에서 비밀 값 가져오기"""
        try:
            if not self.project_id:
                # 환경 변수에서 직접 가져오기 (Docker build 시 설정된 값)
                env_map = {
                    'openai-api-key': 'OPENAI_API_KEY',
                    'gemini-api-key': 'GEMINI_API_KEY',
                    'elevenlabs-api-key': 'ELEVENLABS_API_KEY',
                    'youtube-oauth-credentials': 'YOUTUBE_CREDENTIALS',
                    'storage-bucket-name': 'STORAGE_BUCKET'
                }
                
                if secret_id in env_map:
                    return os.getenv(env_map[secret_id])
            
            # Secret Manager 사용
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
            
        except Exception as e:
            logger.error(f"Secret 가져오기 실패 ({secret_id}): {e}")
            return None
    
    def setup_services(self):
        """서비스 초기화"""
        try:
            logger.info("서비스 초기화 시작...")
            
            # API 키들 가져오기
            openai_api_key = self.get_secret('openai-api-key')
            gemini_api_key = self.get_secret('gemini-api-key')
            elevenlabs_api_key = self.get_secret('elevenlabs-api-key')
            youtube_credentials = self.get_secret('youtube-oauth-credentials')
            
            if not openai_api_key:
                logger.error("OpenAI API 키를 가져올 수 없습니다")
                return False
            
            # Content Generator 초기화
            self.content_generator = ContentGenerator(
                openai_api_key=openai_api_key,
                gemini_api_key=gemini_api_key,
                elevenlabs_api_key=elevenlabs_api_key,
                storage_bucket=self.storage_bucket
            )
            
            # YouTube Uploader 초기화
            if youtube_credentials:
                self.youtube_uploader = YouTubeUploader(
                    credentials_json=youtube_credentials
                )
            else:
                logger.warning("YouTube 인증 정보가 없습니다. 업로드 기능이 비활성화됩니다.")
            
            logger.info("서비스 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"서비스 초기화 실패: {e}")
            logger.error(traceback.format_exc())
            return False

# 전역 인스턴스
automation = YouTubeAutomation()

@app.route('/health', methods=['GET'])
def health_check():
    """헬스체크 엔드포인트"""
    try:
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'content_generator': automation.content_generator is not None,
                'youtube_uploader': automation.youtube_uploader is not None,
                'storage_bucket': automation.storage_bucket is not None
            }
        }
        return jsonify(status), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/generate', methods=['POST'])
def generate_content():
    """컨텐츠 생성 및 업로드"""
    try:
        # 요청 데이터 파싱
        data = request.get_json()
        if not data:
            return jsonify({'error': '요청 데이터가 필요합니다'}), 400
        
        topic = data.get('topic', '유튜브 수익화 팁')
        style = data.get('style', 'informative')
        duration = data.get('duration', 60)
        upload_to_youtube = data.get('upload', True)
        
        logger.info(f"컨텐츠 생성 시작: {topic}")
        
        if not automation.content_generator:
            return jsonify({'error': '컨텐츠 생성기가 초기화되지 않았습니다'}), 500
        
        # 컨텐츠 생성
        result = automation.content_generator.generate_complete_content(
            topic=topic,
            style=style,
            duration=duration
        )
        
        if not result:
            return jsonify({'error': '컨텐츠 생성에 실패했습니다'}), 500
        
        response_data = {
            'status': 'success',
            'message': '컨텐츠 생성 완료',
            'content': {
                'title': result.get('title'),
                'topic': topic,
                'duration': duration,
                'files': {
                    'video': result.get('video_path'),
                    'thumbnail': result.get('thumbnail_path'),
                    'audio': result.get('audio_path')
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # YouTube 업로드
        if upload_to_youtube and automation.youtube_uploader:
            try:
                logger.info("YouTube 업로드 시작...")
                upload_result = automation.youtube_uploader.upload_video(
                    video_path=result['video_path'],
                    title=result['title'],
                    topic=topic,
                    thumbnail_path=result.get('thumbnail_path')
                )
                
                if upload_result:
                    response_data['youtube'] = upload_result
                    logger.info(f"YouTube 업로드 완료: {upload_result['url']}")
                else:
                    response_data['youtube_error'] = 'YouTube 업로드에 실패했습니다'
                    logger.error("YouTube 업로드 실패")
                    
            except Exception as e:
                logger.error(f"YouTube 업로드 오류: {e}")
                response_data['youtube_error'] = str(e)
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"컨텐츠 생성 오류: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': '컨텐츠 생성 중 오류가 발생했습니다',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """현재 상태 조회"""
    try:
        channel_info = None
        if automation.youtube_uploader:
            channel_info = automation.youtube_uploader.get_channel_info()
        
        return jsonify({
            'status': 'running',
            'services': {
                'content_generator': automation.content_generator is not None,
                'youtube_uploader': automation.youtube_uploader is not None
            },
            'channel_info': channel_info,
            'project_id': automation.project_id,
            'storage_bucket': automation.storage_bucket,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"상태 조회 오류: {e}")
        return jsonify({
            'error': '상태 조회 중 오류가 발생했습니다',
            'details': str(e)
        }), 500

@app.route('/topics', methods=['GET'])
def get_trending_topics():
    """인기 주제 목록 반환"""
    topics = [
        "유튜브 수익화 완벽 가이드",
        "집에서 월 100만원 벌기",
        "부업으로 시작하는 온라인 사업",
        "투자 초보자를 위한 가이드",
        "시간 관리의 비밀",
        "효율적인 공부법",
        "건강한 다이어트 방법",
        "인공지능 활용법",
        "소셜미디어 마케팅 전략",
        "창업 아이디어 10가지"
    ]
    
    return jsonify({
        'topics': topics,
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/', methods=['GET'])
def home():
    """홈페이지"""
    return jsonify({
        'service': 'GCP YouTube Automation',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'generate': '/generate (POST)',
            'status': '/status',
            'topics': '/topics'
        },
        'timestamp': datetime.now().isoformat()
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    # 개발 환경에서 실행
    app.run(host='0.0.0.0', port=8080, debug=False)
