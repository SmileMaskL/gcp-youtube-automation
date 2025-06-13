import os
import json
import random
import time
from content_generator import generate_content
from video_creator import create_video
from thumbnail_generator import generate_thumbnail
from youtube_uploader import upload_to_youtube

def load_environment():
    """환경변수 로드 (간소화 버전)"""
    try:
        openai_keys = json.loads(os.getenv("OPENAI_KEYS_JSON", "[]"))
        if not openai_keys:
            raise ValueError("OpenAI 키가 없습니다.")
        
        os.environ.update({
            'OPENAI_API_KEY': random.choice(openai_keys),
            'GEMINI_API_KEY': os.getenv("GEMINI_API_KEY", ""),
            'ELEVENLABS_API_KEY': os.getenv("ELEVENLABS_API_KEY", ""),
            'PEXELS_API_KEY': os.getenv("PEXELS_API_KEY", ""),
            'YOUTUBE_OAUTH_CREDENTIALS': os.getenv("YOUTUBE_OAUTH_CREDENTIALS", "{}")
        })
        
        # Gemini API 키가 있는지 확인
        if not os.getenv("GEMINI_API_KEY"):
            print("ℹ️ GEMINI_API_KEY가 설정되지 않았습니다. Gemini 기능을 사용할 수 없습니다.")
            
        return True
    except Exception as e:
        print(f"❌ 환경 설정 오류: {e}")
        return False

def main():
    print("="*50)
    print("🎬 유튜브 자동화 시스템 시작 (v2.1)")  # 버전 업데이트
    print("="*50)
    
    if not load_environment():
        return

    # 실제 수익 나는 주제 5개
    topics = [
        "AI로 월 100만원 버는 실제 방법 2025",
        "유튜브 자동화 무료 도구 TOP5",
        "구글 클라우드 무료 크레딧 사용법",
        "ChatGPT로 수익 창출한 사례 3가지",
        "집에서 하는 부업 추천 (초보자용)"
    ]

    for topic in topics:
        print(f"\n🔥 [{topics.index(topic)+1}/{len(topics)}] 주제: {topic}")
        
        try:
            start_time = time.time()
            script = generate_content(topic)
            if not script:
                print(f"❌ 대본 생성 실패: {topic}")
                continue
                
            print(f"✅ 대본 생성 완료 ({len(script)}자) - 소요시간: {time.time()-start_time:.2f}초")
            
            video_path = create_video(script, topic)
            thumbnail_path = generate_thumbnail(topic)
            upload_to_youtube(video_path, thumbnail_path, topic)
            
        except Exception as e:
            print(f"❌ '{topic}' 처리 실패: {str(e)[:100]}...")
            continue

if __name__ == "__main__":
    main()
