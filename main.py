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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class YouTubeAutomationService:
    def __init__(self):
        self.project_id = os.environ.get('PROJECT_ID', 'youtube-fully-automated')
        self.secret_client = secretmanager.SecretManagerServiceClient()
        self.secrets = {}
        self._load_secrets()
        
    def _load_secrets(self):
        """GCP Secret Manager에서 시크릿 로드"""
        secret_names = [
            'PEXELS_API_KEY',
            'OPENAI_API_KEYS', 
            'GEMINI_API_KEY',
            'ELEVENLABS_API_KEY',
            'YOUTUBE_CLIENT_ID',
            'YOUTUBE_CLIENT_SECRET',
            'YOUTUBE_REFRESH_TOKEN'
        ]
        
        for secret_name in secret_names:
            try:
                name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
                response = self.secret_client.access_secret_version(request={"name": name})
                self.secrets[secret_name] = response.payload.data.decode("UTF-8")
                logger.info(f"✅ {secret_name} 시크릿 로드 완료")
            except Exception as e:
                logger.error(f"❌ {secret_name} 시크릿 로드 실패: {str(e)}")
                
    def generate_content(self, topics=None):
        """컨텐츠 생성"""
        try:
            if not topics:
                topics = [
                    "최신 AI 기술 동향과 수익 창출 방법",
                    "프로그래밍으로 부업하는 5가지 방법", 
                    "창업 성공을 위한 필수 마인드셋",
                    "투자 초보자를 위한 안전한 투자 전략",
                    "온라인 비즈니스 시작하는 완벽 가이드",
                    "부동산 투자의 숨겨진 수익 포인트",
                    "디지털 마케팅으로 월 100만원 벌기",
                    "코딩 부트캠프 vs 독학, 어떤 게 더 효과적일까"
                ]
            
            generator = ContentGenerator(
                pexels_api_key=self.secrets.get('PEXELS_API_KEY'),
                openai_api_key=self.secrets.get('OPENAI_API_KEYS'),
                gemini_api_key=self.secrets.get('GEMINI_API_KEY'),
                elevenlabs_api_key=self.secrets.get('ELEVENLABS_API_KEY'),
                elevenlabs_voice_id='uyVNoMrnUku1dZyVEXwD'  # 안나 킴 목소리
            )
            
            # 랜덤하게 주제 선택
            import random
            selected_topic = random.choice(topics)
            
            logger.info(f"🎯 선택된 주제: {selected_topic}")
            
            # 컨텐츠 생성
            video_data = generator.generate_video_content(selected_topic)
            
            if video_data:
                logger.info("✅ 비디오 컨텐츠 생성 완료")
                return video_data
            else:
                logger.error("❌ 비디오 컨텐츠 생성 실패")
                return None
                
        except Exception as e:
            logger.error(f"❌ 컨텐츠 생성 중 오류: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def upload_to_youtube(self, video_data):
        """YouTube에 업로드"""
        try:
            uploader = YouTubeUploader(
                client_id=self.secrets.get('YOUTUBE_CLIENT_ID'),
                client_secret=self.secrets.get('YOUTUBE_CLIENT_SECRET'),
                refresh_token=self.secrets.get('YOUTUBE_REFRESH_TOKEN')
            )
            
            # 업로드 메타데이터 준비
            upload_data = {
                'title': video_data.get('title', 'AI가 만든 수익형 컨텐츠'),
                'description': video_data.get('description', ''),
                'tags': video_data.get('tags', ['AI', '수익창출', '부업', '투자']),
                'video_path': video_data.get('video_path'),
                'thumbnail_path': video_data.get('thumbnail_path')
            }
            
            # YouTube 업로드
            video_id = uploader.upload_video(upload_data)
            
            if video_id:
                logger.info(f"✅ YouTube 업로드 완료: {video_id}")
                return video_id
            else:
                logger.error("❌ YouTube 업로드 실패")
                return None
                
        except Exception as e:
            logger.error(f"❌ YouTube 업로드 중 오류: {str(e)}")
            logger.error(traceback.format_exc())
            return None

# 서비스 인스턴스 생성
automation_service = YouTubeAutomationService()

@app.route('/', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        'status': 'ok',
        'message': 'YouTube Automation Service is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """상태 확인"""
    return jsonify({
        'status': 'active',
        'service': 'YouTube Automation',
        'secrets_loaded': len(automation_service.secrets),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/content/generate', methods=['POST'])
def generate_and_upload():
    """컨텐츠 생성 및 YouTube 업로드"""
    try:
        data = request.get_json() or {}
        topics = data.get('topics')
        
        logger.info("🚀 컨텐츠 생성 및 업로드 시작")
        
        # 1. 컨텐츠 생성
        video_data = automation_service.generate_content(topics)
        if not video_data:
            return jsonify({
                'success': False,
                'error': '컨텐츠 생성 실패'
            }), 500
        
        # 2. YouTube 업로드
        video_id = automation_service.upload_to_youtube(video_data)
        if not video_id:
            return jsonify({
                'success': False,
                'error': 'YouTube 업로드 실패'
            }), 500
        
        logger.info("🎉 전체 프로세스 완료")
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'title': video_data.get('title'),
            'youtube_url': f'https://www.youtube.com/watch?v={video_id}',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ API 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/status', methods=['POST'])
def status_endpoint():
    """기존 status 엔드포인트 (하위 호환성)"""
    return jsonify({
        'status': 'ok',
        'message': 'Service is running',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
