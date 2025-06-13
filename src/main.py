import os
import json
import random
from content_generator import generate_content
from video_creator import create_video
from thumbnail_generator import generate_thumbnail
from youtube_uploader import upload_to_youtube

def load_environment():
    """환경변수에서 모든 설정을 로드"""
    try:
        # OpenAI 키 (여러 개 가능)
        openai_keys = json.loads(os.getenv("OPENAI_KEYS_JSON", "[]"))
        if not openai_keys:
            raise ValueError("OpenAI 키가 없습니다.")
        
        # 다른 API 키들
        env_vars = {
            'OPENAI_API_KEY': random.choice(openai_keys),
            'GEMINI_API_KEY': os.getenv("GEMINI_API_KEY", ""),
            'ELEVENLABS_API_KEY': os.getenv("ELEVENLABS_API_KEY", ""),
            'PEXELS_API_KEY': os.getenv("PEXELS_API_KEY", ""),
            'YOUTUBE_OAUTH_CREDENTIALS': os.getenv("YOUTUBE_OAUTH_CREDENTIALS", "{}")
        }
        
        # 환경변수 설정
        for key, value in env_vars.items():
            os.environ[key] = value
        
        return env_vars
    except Exception as e:
        print(f"❌ 환경 설정 오류: {e}")
        return None

def main():
    print("="*50)
    print("🎬 유튜브 자동화 시스템 시작!")
    print("="*50)
    
    # 1. 환경 설정
    env = load_environment()
    if not env:
        return

    print(f"🔑 사용된 OpenAI 키: {env['OPENAI_API_KEY'][:5]}...")
    print(f"🌐 다른 API 키들 로드 완료")

    # 2. 인기 주제 리스트 (실제 수익 잘 나는 주제들)
    money_making_topics = [
        "AI로 월 100만원 버는 법 2024",
        "유튜브 자동화 무료 도구 5가지",
        "구글 클라우드 무료 사용 꿀팁",
        "ChatGPT로 돈 버는 실제 사례",
        "집에서 하는 부업 추천 2024"
    ]

    # 3. 각 주제별로 콘텐츠 생성 → 영상 제작 → 업로드
    for topic in money_making_topics:
        print(f"\n🔥 주제: {topic}")
        
        try:
            # 콘텐츠 생성
            script = generate_content(topic)
            print("✅ 콘텐츠 생성 완료")
            
            # 영상 제작
            video_file = create_video(script, topic)
            print(f"✅ 영상 생성 완료: {video_file}")
            
            # 썸네일 생성
            thumbnail = generate_thumbnail(topic)
            print(f"✅ 썸네일 생성 완료: {thumbnail}")
            
            # 유튜브 업로드
            upload_to_youtube(video_file, thumbnail, topic)
            print("✅ 유튜브 업로드 완료")
        except Exception as e:
            print(f"❌ 주제 '{topic}' 처리 중 오류: {e}")
            continue

if __name__ == "__main__":
    main()
