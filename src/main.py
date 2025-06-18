import os
import sys
import logging
from fastapi import FastAPI
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 내 src 모듈 참조 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent))

# 환경변수 로드
load_dotenv()

# FastAPI 인스턴스 생성 (반드시 최상단)
app = FastAPI()

# 포트 설정
PORT = int(os.getenv("PORT", "8080"))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Health Check 엔드포인트
@app.get("/health")
def health_check():
    logger.info(f"✅ Health check OK on port {PORT}")
    return {"status": "ok", "port": PORT}

@app.get("/")
def home():
    return {"message": "🚀 YouTube Automation is running on Cloud Run"}

# 기본 기능 모듈 로드
from src.config import Config
from src.content_generator import ShortsGenerator
from src.tts_generator import text_to_speech
from src.bg_downloader import download_background_video
from src.video_editor import create_video
from src.thumbnail_generator import create_thumbnail
from src.youtube_uploader import upload_to_youtube

def cleanup_temp_files():
    for file in Config.TEMP_DIR.glob("*"):
        try:
            if file.is_file():
                file.unlink()
        except Exception as e:
            logger.error(f"임시 파일 삭제 실패 {file}: {e}")

def check_environment():
    required_vars = {
        'GEMINI_API_KEY': 'Google Gemini API 키',
        'ELEVENLABS_API_KEY': 'ElevenLabs API 키',
        'PEXELS_API_KEY': 'Pexels API 키'
    }
    missing = [name for name, desc in required_vars.items() if not os.getenv(name)]
    if missing:
        logger.error(f"다음 환경변수가 필요합니다: {', '.join(missing)}")
        return False
    return True

def main():
    try:
        Config.ensure_directories()
        logger.info("=" * 50)
        logger.info("💰 유튜브 자동화 시스템 시작 💰")
        logger.info("=" * 50)

        if not check_environment():
            return

        generator = ShortsGenerator()
        contents = generator.generate_daily_contents()
        for content in contents:
            try:
                logger.info(f"📌 주제: {content['title']}")

                audio_path = Config.TEMP_DIR / "output_audio.mp3"
                text_to_speech(content['script'], str(audio_path))

                bg_video = download_background_video(content['video_query'])
                output_vid = Config.OUTPUT_DIR / f"final_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
                create_video(str(bg_video), str(audio_path), str(output_vid))

                thumbnail = Config.OUTPUT_DIR / "thumbnail.jpg"
                create_thumbnail(content['title'], str(bg_video), str(thumbnail))

                if upload_to_youtube(str(output_vid), content['title']):
                    logger.info(f"✅ 업로드 완료: {content['title']}")

            except Exception as e:
                logger.error(f"❌ 처리 중 오류: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"❌ 시스템 전체 오류: {e}", exc_info=True)
    finally:
        cleanup_temp_files()

if __name__ == "__main__":
    import uvicorn
    logger.info(f"⚙️ FastAPI 서버 실행 on port {PORT}")
    uvicorn.run("src.main:app", host="0.0.0.0", port=PORT, reload=False)
