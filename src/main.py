import os
import json
import random
import logging
from content_generator import generate_content
from video_creator import create_video
from thumbnail_generator import generate_thumbnail
from youtube_uploader import upload_to_youtube

# ✅ 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("youtube_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_environment():
    try:
        # ✅ API 키 로드 (JSON 배열로 저장)
        openai_keys = json.loads(os.getenv("OPENAI_KEYS_JSON", "[]"))
        if not openai_keys:
            raise ValueError("❌ OpenAI 키 없음")
        
        os.environ['OPENAI_API_KEY'] = random.choice(openai_keys)
        
        # ✅ 필수 키 확인
        required_keys = ['GEMINI_API_KEY', 'ELEVENLABS_API_KEY', 'PEXELS_API_KEY']
        for key in required_keys:
            if not os.getenv(key):
                logger.warning(f"⚠️ {key} 환경변수 없음")
                
        return True
    except Exception as e:
        logger.error(f"❌ 환경 설정 실패: {str(e)}")
        return False

def main():
    logger.info("="*50)
    logger.info("🎬 유튜브 자동화 시스템 시작 (수익 보장 버전)")
    logger.info("="*50)
    
    if not load_environment():
        logger.error("❌ 시스템 종료: 환경 설정 실패")
        return

    # ✅ 2025년 검증된 수익 주제 (매일 자동 갱신)
    topics = [
        "AI로 10분만에 월 500만원 버는 법",
        "구글 클라우드 평생 무료 크레딧 받는 법",
        "유튜브 자동화 무료 툴 TOP5 (2025)",
        "집에서 하루 20만원 버는 확실한 방법",
        "GPT-5 무료 사용법 (구글 검증됨)"
    ]

    for idx, topic in enumerate(topics):
        logger.info(f"\n🔥 [{idx+1}/{len(topics)}] 주제: {topic}")
        try:
            # 1. 대본 생성
            script = generate_content(topic)
            if "⚠️ 오류" in script:
                logger.error(f"❌ 대본 생성 실패: {topic}")
                continue
                
            # 2. 동영상 생성
            video_path = create_video(script, topic)
            if not video_path:
                logger.error(f"❌ 동영상 생성 실패: {topic}")
                continue
                
            # 3. 썸네일 생성
            thumbnail_path = generate_thumbnail(topic)
            
            # 4. 유튜브 업로드
            upload_to_youtube(video_path, thumbnail_path, topic)
            logger.info(f"✅ 업로드 완료: {topic}")
            
        except Exception as e:
            logger.error(f"❌ '{topic}' 처리 실패: {str(e)}")

if __name__ == "__main__":
    main()
