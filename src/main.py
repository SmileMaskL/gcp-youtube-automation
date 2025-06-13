import os
import json
import random
import logging
import sys

# 🔥 모듈 임포트 에러를 더 명확하게 보기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_generator import generate_content
from video_creator import create_video
# 썸네일과 유튜브 업로더는 기능이 준비되었다고 가정합니다.
# from thumbnail_generator import generate_thumbnail
# from youtube_uploader import upload_to_youtube

# 로깅 설정: 파일과 콘솔에 모두 출력
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
        # OpenAI 키는 여러 개를 JSON 배열 형태로 관리하여 순환 사용
        openai_keys_str = os.getenv("OPENAI_KEYS_JSON")
        if openai_keys_str:
            openai_keys = json.loads(openai_keys_str)
            if openai_keys:
                os.environ['OPENAI_API_KEY'] = random.choice(openai_keys)
                logger.info("✅ OpenAI API 키 로드 성공")
        else:
            logger.warning("⚠️ OPENAI_KEYS_JSON 환경변수가 없습니다.")

        # 다른 필수 키 확인 (없으면 경고만)
        required_keys = ['GEMINI_API_KEY', 'ELEVENLABS_API_KEY', 'PEXELS_API_KEY']
        for key in required_keys:
            if not os.getenv(key):
                logger.warning(f"⚠️ {key} 환경변수가 없습니다.")
        return True
    except Exception as e:
        logger.error(f"❌ 환경 설정 실패: {str(e)}")
        return False

def main():
    logger.info("="*50)
    logger.info("🎬 유튜브 자동화 시스템 시작 (수익 극대화 최종 버전)")
    logger.info("="*50)

    if not load_environment():
        logger.error("❌ 시스템 종료: 환경 설정 실패")
        return

    # 🔥 2025년 6월, 구글 트렌드 기반 수익형 주제 (즉시 사용 가능)
    topics = [
        "GPT-4o로 10분만에 쇼츠 영상 만들고 월 300만원 버는 법",
        "구글 제미나이, 모르면 손해인 무료 AI 기능 TOP 5",
        "클로드 3.5 소네트, ChatGPT를 이길 수 있을까? (충격적인 결과)",
        "무료 AI 그림 도구, '미드저니' 뛰어넘는 3가지 추천",
        "직장인 AI 부업, 실제로 월 100만원 이상 버는 사람들 특징"
    ]

    for idx, topic in enumerate(topics):
        logger.info(f"\n🔥 [{idx+1}/{len(topics)}] 주제 처리 시작: {topic}")
        try:
            # 1. 대본 생성 (AI 사용)
            # generate_content 함수는 content_generator.py에 정의되어 있어야 합니다.
            # 여기서는 예시로 스크립트를 직접 만듭니다.
            script = f"안녕하세요! 오늘은 '{topic}'에 대해 알아보겠습니다. 이 방법은 정말 놀랍습니다..."
            logger.info("✅ 대본 생성 완료")
            
            # 2. 동영상 생성
            video_path = create_video(script, topic)
            if not video_path:
                logger.error(f"❌ 동영상 생성 실패: {topic}")
                continue # 다음 주제로 넘어감

            # 3. 썸네일 생성 (기능 구현 필요)
            # thumbnail_path = generate_thumbnail(topic)
            logger.info("✅ (가상) 썸네일 생성 완료")
            
            # 4. 유튜브 업로드 (기능 구현 필요)
            # upload_to_youtube(video_path, "썸네일경로", topic)
            logger.info(f"✅ (가상) 유튜브 업로드 완료: {topic}")
            logger.info(f"🎉 성공! 영상 파일 경로: {video_path}")

        except Exception as e:
            logger.error(f"❌ '{topic}' 주제 처리 중 심각한 오류 발생: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
