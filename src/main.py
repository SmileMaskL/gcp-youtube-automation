import os
import json
import random
from content_generator import generate_content
from video_creator import create_video
from thumbnail_generator import generate_thumbnail
from youtube_uploader import upload_to_youtube

class APIKeyManager:
    def __init__(self):
        pass

    def get_openai_keys(self):
        try:
            keys = json.loads(os.getenv("OPENAI_KEYS_JSON", "[]"))
            if not isinstance(keys, list):
                raise ValueError("OPENAI_KEYS_JSON must be a JSON array.")
            return keys
        except Exception as e:
            print(f"❌ OpenAI API 키 파싱 오류: {e}")
            return []

    def get_other_api_keys(self):
        return {
            'gemini': os.getenv("GEMINI_API_KEY", ""),
            'elevenlabs': os.getenv("ELEVENLABS_API_KEY", ""),
            'pexels': os.getenv("PEXELS_API_KEY", ""),
            'youtube': os.getenv("YOUTUBE_OAUTH_CREDENTIALS", "{}")
        }

def parse_youtube_credentials(credentials_str):
    try:
        return json.loads(credentials_str)
    except json.JSONDecodeError:
        return {
            "client_id": os.getenv("YOUTUBE_CLIENT_ID", ""),
            "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET", ""),
            "refresh_token": os.getenv("YOUTUBE_REFRESH_TOKEN", "")
        }

def main():
    api_manager = APIKeyManager()

    openai_keys = api_manager.get_openai_keys()
    if not openai_keys:
        print("⚠️ OpenAI API 키가 없습니다. 종료합니다.")
        return

    other_keys = api_manager.get_other_api_keys()
    youtube_creds = parse_youtube_credentials(other_keys.get('youtube', '{}'))

    openai_api_key = random.choice(openai_keys)
    os.environ.update({
        'OPENAI_API_KEY': openai_api_key,
        'GEMINI_API_KEY': other_keys.get('gemini', ''),
        'ELEVENLABS_API_KEY': other_keys.get('elevenlabs', ''),
        'PEXELS_API_KEY': other_keys.get('pexels', ''),
        'YOUTUBE_CLIENT_ID': youtube_creds.get('client_id', ''),
        'YOUTUBE_CLIENT_SECRET': youtube_creds.get('client_secret', ''),
        'YOUTUBE_REFRESH_TOKEN': youtube_creds.get('refresh_token', '')
    })

    print("="*50)
    print(f"✅ 선택된 OpenAI API 키: {openai_api_key[:10]}... (총 {len(openai_keys)}개 중 1개 사용)")
    print("="*50)

    topics = [
        "GCP로 유튜브 자동화 마스터하기",
        "AI로 월 1000만원 버는 방법",
        "ChatGPT 5.0 실전 활용법",
        "구글 제미니 고급 프로덕트 리뷰",
        "무료 클라우드로 수익 창출"
    ]

    for i, topic in enumerate(topics):
        print(f"\n🎬 [{i+1}/{len(topics)}] 주제: {topic}")
        content_text = generate_content(topic)
        print(f"✍️ 콘텐츠 생성 완료")

        video_path = create_video(content_text, topic)
        print(f"🎞️ 영상 생성 완료: {video_path}")

        thumbnail_path = generate_thumbnail(topic)
        print(f"🖼️ 썸네일 생성 완료: {thumbnail_path}")

        upload_to_youtube(video_path, thumbnail_path, topic)
        print(f"🚀 유튜브 업로드 완료: {topic}")

if __name__ == "__main__":
    main()
