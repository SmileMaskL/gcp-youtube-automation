"""
유튜브 자동화 메인 시스템 (무조건 실행되는 버전)
"""
import os
import sys
import logging
import random
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.utils import (
    generate_viral_content_gemini,
    generate_tts_with_elevenlabs,
    download_video_from_pexels,
    create_shorts_video,
    cleanup_temp_files
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_DIR / "youtube_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """필수 환경변수 확인"""
    required_vars = {
        'GEMINI_API_KEY': 'Google Gemini API 키',
        'ELEVENLABS_API_KEY': 'ElevenLabs API 키'
    }
    
    missing_vars = []
    for var, name in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(name)
    
    if missing_vars:
        logger.error(f"다음 환경변수가 필요합니다: {', '.join(missing_vars)}")
        logger.error(".env 파일을 확인해주세요.")
        return False
    return True

def generate_daily_topic():
    """매일 다른 주제 생성"""
    topics = [
        "부자가 되는 습관 5가지",
        "성공하는 사람들의 아침 루틴",
        "돈 버는 부업 아이디어 2025",
        "초보자도 할 수 있는 투자 방법",
        "시간 관리의 비밀",
        "생산성을 높이는 방법",
        "스트레스 해소 기술",
        "건강한 삶을 위한 팁",
        "인간관계 개선 방법",
        "자기계발 필수 습관"
    ]
    return random.choice(topics)

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
        topic = generate_daily_topic()
        logger.info(f"🔥 오늘의 주제: {topic}")
        
        content = generate_viral_content_gemini(topic)
        logger.info(f"📌 제목: {content['title']}")
        logger.info(f"📜 대본 길이: {len(content['script'])}자")
        
        # 4. 음성 생성
        audio_path = generate_tts_with_elevenlabs(content['script'])
        logger.info(f"🔊 음성 파일 생성: {audio_path}")
        
        # 5. 영상 다운로드
        video_path = download_video_from_pexels(topic, duration=60)
        logger.info(f"🎬 배경 영상 준비: {video_path}")
        
        # 6. 최종 영상 생성
        final_path = create_shorts_video(video_path, audio_path, content['title'])
        logger.info(f"✅ 최종 영상 생성: {final_path}")
        
        # 7. 정리 작업
        cleanup_temp_files()
        
        logger.info("=" * 50)
        logger.info("🎉 모든 작업이 완료되었습니다!")
        logger.info(f"📁 영상 경로: {final_path}")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {str(e)}", exc_info=True)
    finally:
        cleanup_temp_files()

if __name__ == "__main__":
    main()
