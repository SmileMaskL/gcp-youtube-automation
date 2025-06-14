import os
import logging
import time
from pathlib import Path
from utils import (
    generate_viral_content,
    text_to_speech,
    download_video_from_pexels,
    add_text_to_clip,
    Config
)
from youtube_uploader import upload_video

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("youtube_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_hot_topics():
    """수익형 키워드 자동 생성 (Gemini 활용)"""
    try:
        if not Config.GEMINI_API_KEY:
            return ["돈 버는 방법", "부자 되는 비밀", "주식 투자", "부동산 수익", "온라인 수익 창출"]

        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            "2025년 한국에서 가장 인기 있을 5가지 수익형 유튜브 쇼츠 주제를 JSON 배열로 출력해주세요."
        )
        return json.loads(response.text.strip("```json").strip())
    except:
        return ["부자 되는 습관", "주식 초보 탈출", "월 1000만원 버는 법", "재테크 비법", "유튜브 수익 창출"]

def main():
    logger.info("="*50)
    logger.info("💰 유튜브 수익형 자동화 시스템 시작")
    logger.info("="*50)

    # 필수 환경 변수 확인
    if not Config.validate():
        logger.error("❌ 필수 API 키가 설정되지 않았습니다.")
        return

    # 1. 인기 주제 수집
    topics = get_hot_topics()
    logger.info(f"🔥 오늘의 수익형 주제: {', '.join(topics)}")

    # 2. 주제별 영상 제작
    for topic in topics:
        try:
            logger.info(f"\n📌 주제 처리 시작: {topic}")
            
            # 콘텐츠 생성
            content = generate_viral_content(topic)
            if len(content["script"]) < 50:
                raise ValueError("대본이 너무 짧습니다.")

            # 음성 생성
            audio_path = text_to_speech(content["script"])
            
            # 영상 다운로드
            video_path = download_video_from_pexels(topic)
            
            # 영상 편집
            final_path = f"output/{uuid.uuid4()}.mp4"
            add_text_to_clip(video_path, content["title"], final_path)

            # 업로드
            upload_video(
                video_path=final_path,
                title=f"{content['title']} 💰",
                description=f"{content['script']}\n\n{' '.join(content['hashtags'])}",
                tags=content["hashtags"],
                privacy_status="public"
            )

            time.sleep(10)  # API Rate Limit 방지

        except Exception as e:
            logger.error(f"❌ {topic} 처리 실패: {str(e)}")
            continue

    logger.info("\n🎉 모든 영상 업로드 완료!")

if __name__ == "__main__":
    main()
