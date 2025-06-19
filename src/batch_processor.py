#!/usr/bin/env python3
import os
import sys
import logging
from datetime import datetime
from google.cloud import secretmanager
from src.content_generator import ContentGenerator
from src.video_creator import VideoCreator
from src.youtube_uploader import YouTubeUploader
from src.error_handler import ErrorHandler
from src.monitoring import log_system_health
from src.usage_tracker import UsageTracker
from src.ai_rotation import AIRotation

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/youtube_shorts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.usage_tracker = UsageTracker()
        self.ai_rotation = AIRotation()
        self.config = self._load_config()
        
    def _load_config(self):
        """GCP Secret Manager에서 설정 로드"""
        try:
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv('GCP_PROJECT_ID')
            
            secrets = {
                'OPENAI_API_KEYS': self._get_secret(client, project_id, 'openai-api-keys'),
                'GEMINI_API_KEY': self._get_secret(client, project_id, 'gemini-api-key'),
                'ELEVENLABS_API_KEY': self._get_secret(client, project_id, 'elevenlabs-api-key'),
                'PEXELS_API_KEY': self._get_secret(client, project_id, 'pexels-api-key'),
                'YOUTUBE_CREDENTIALS': self._get_secret(client, project_id, 'youtube-oauth-credentials')
            }
            
            return {
                'ai_type': 'gpt-4o',
                'output_dir': os.getenv('OUTPUT_DIR', 'output'),
                'max_retries': 3,
                **secrets
            }
        except Exception as e:
            logger.error(f"설정 로드 실패: {e}")
            return self._load_fallback_config()

    def _get_secret(self, client, project_id, secret_id):
        """GCP Secret Manager에서 개별 시크릿 가져오기"""
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")

    def _load_fallback_config(self):
        """시크릿 관리자 실패 시 환경 변수 사용"""
        return {
            'OPENAI_API_KEYS': os.getenv('OPENAI_API_KEYS', '').split(','),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
            'ELEVENLABS_API_KEY': os.getenv('ELEVENLABS_API_KEY'),
            'PEXELS_API_KEY': os.getenv('PEXELS_API_KEY'),
            'YOUTUBE_CREDENTIALS': os.getenv('YOUTUBE_OAUTH_CREDENTIALS'),
            'ai_type': 'gpt-4o',
            'output_dir': os.getenv('OUTPUT_DIR', 'output'),
            'max_retries': 3
        }

    def process(self):
        """배치 처리 메인 로직"""
        try:
            logger.info("🎬 콘텐츠 생성 시작")
            
            # API 키 로테이션 적용
            current_key = self.ai_rotation.get_next_key()
            os.environ['OPENAI_API_KEY'] = current_key
            
            # 1. 콘텐츠 생성
            generator = ContentGenerator()
            script = generator.generate_script()
            
            if not script or not script.get('script'):
                raise ValueError("생성된 스크립트가 유효하지 않습니다.")
            
            # 2. 영상 제작
            video_creator = VideoCreator()
            video_path = video_creator.create_video(
                script=script['script'],
                output_dir=self.config['output_dir'],
                voice_id=os.getenv('ELEVENLABS_VOICE_ID', 'uyVNoMrnUku1dZyVEXwD'),
                font_path=os.getenv('FONT_PATH', './fonts/Catfont.ttf')
            )
            
            if not video_path:
                raise ValueError("영상 생성 실패")
                
            # 3. 유튜브 업로드
            uploader = YouTubeUploader(self.config['YOUTUBE_CREDENTIALS'])
            upload_result = uploader.upload_video(
                video_path=video_path,
                title=script['topic'][:100],
                description=script['script'][:5000]
            )
            
            logger.info(f"✅ 업로드 성공: {upload_result['video_id']}")
            return True
            
        except Exception as e:
            self.error_handler.handle(e)
            return False

def main():
    """메인 실행 함수"""
    log_system_health()
    
    processor = BatchProcessor()
    success = processor.process()
    
    if not success:
        logger.error("❌ 배치 처리 실패")
        sys.exit(1)
        
    logger.info("🎉 배치 처리 완료")

if __name__ == "__main__":
    main()
