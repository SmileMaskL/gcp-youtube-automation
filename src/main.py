"""
유튜브 자동화 메인 시스템 (무조건 실행되는 버전)
"""
from fastapi import FastAPI
import os
import sys
import logging
import json
import random
from .content_generator import ShortsGenerator
from .config import Config
from .ai_rotation import AIClient
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from .video_editor import create_video

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.content_generator import ShortsGenerator
from src.tts_generator import text_to_speech
from src.bg_downloader import download_background_video
from src.video_editor import create_video
from src.thumbnail_generator import create_thumbnail
from src.youtube_uploader import upload_to_youtube

app = FastAPI()

# 포트 설정
PORT = int(os.getenv('PORT', '8080'))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Health Check 엔드포인트
@app.get('/health')
def health_check():
    logger.info(f"✅ Health check OK on port {PORT}")
    return {'status': 'ok', 'port': PORT}

@app.get('/')
def home():
    return {'message': '🚀 YouTube Automation is running on Cloud Run'}
if __name__ == '__main__':
    import uvicorn
    logger.info(f"🚀 FastAPI 서버 실행 on port {PORT}")
    uvicorn.run("src.main:app", host="0.0.0.0", port=PORT, reload=False)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

app = FastAPI()

def cleanup_temp_files():
    """임시 파일 정리"""
    for file in Config.TEMP_DIR.glob("*"):
        try:
            if file.is_file():
                file.unlink()
        except Exception as e:
            logger.error(f"임시 파일 삭제 실패 {file}: {e}")

def check_environment():
    """필수 환경변수 확인"""
    required_vars = {
        'GEMINI_API_KEY': 'Google Gemini API 키',
        'ELEVENLABS_API_KEY': 'ElevenLabs API 키',
        'PEXELS_API_KEY': 'Pexels API 키'
    }
    
    missing_vars = [name for var, name in required_vars.items() if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"다음 환경변수가 필요합니다: {', '.join(missing_vars)}")
        return False
    return True

def main():
    try:
        # 1. 환경 설정
        load_dotenv()
        Config.ensure_directories()
        
        logger.info("=" * 50)
        logger.info("💰 유튜브 수익형 자동화 시스템 시작 💰")
        logger.info("=" * 50)
        
        # 2. 환경변수 확인
        if not check_environment():
            return
        
        # 3. 콘텐츠 생성
        generator = ShortsGenerator()
        contents = generator.generate_daily_contents()
        
        for content in contents:
            try:
                logger.info(f"📌 처리 중인 주제: {content['title']}")
                
                # 4. 음성 생성
                audio_path = Config.TEMP_DIR / "output_audio.mp3"
                text_to_speech(content['script'], str(audio_path))
                
                # 5. 배경 영상 다운로드
                bg_video_path = download_background_video(content['video_query'])
                
                # 6. 영상 편집
                output_video_path = Config.OUTPUT_DIR / f"final_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
                create_video(str(bg_video_path), str(audio_path), str(output_video_path))
                
                # 7. 썸네일 생성
                thumbnail_path = Config.OUTPUT_DIR / "thumbnail.jpg"
                create_thumbnail(content['title'], str(bg_video_path), str(thumbnail_path))
                
                # 8. 유튜브 업로드
                if upload_to_youtube(str(output_video_path), content['title']):
                    logger.info(f"성공적으로 업로드 완료: {content['title']}")
                
            except Exception as e:
                logger.error(f"주제 '{content['title']}' 처리 중 오류: {e}")
                continue
        
        logger.info("=" * 50)
        logger.info("🎉 모든 작업이 완료되었습니다!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ 시스템 오류 발생: {str(e)}", exc_info=True)
    finally:
        cleanup_temp_files()

if __name__ == "__main__":
    main()
