import os
import json
import random
from google.cloud import secretmanager
from content_generator import generate_content
from video_creator import create_video
from thumbnail_generator import generate_thumbnail
from youtube_uploader import upload_to_youtube

class APIKeyManager:
    def __init__(self, project_id="youtube-fully-automated"):
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id

    def get_secret(self, secret_id):
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
        response = self.client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")

    def get_openai_keys(self):
        try:
            keys_json = self.get_secret("openai-api-keys")
            keys = json.loads(keys_json)
            if not isinstance(keys, list):
                raise ValueError("OpenAI keys secret must be a JSON array.")
            return keys
        except Exception as e:
            print(f"❌ OpenAI API 키 파싱 실패: {e}")
            return []

    def get_other_api_keys(self):
        secrets = {
            "gemini": "gemini-api-key",
            "elevenlabs": "elevenlabs-api-key",
            "pexels": "pexels-api-key",
            "youtube": "youtube-oauth-credentials"
        }
        results = {}
        for k, sid in secrets.items():
            try:
                results[k] = self.get_secret(sid)
            except Exception as e:
                print(f"❌ {k} 키 로딩 실패: {e}")
                results[k] = ""
        return results

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
    PROJECT_ID = "youtube-fully-automated"
    api_manager = APIKeyManager(PROJECT_ID)

    openai_keys = api_manager.get_openai_keys()
    if not openai_keys:
        print("❌ OpenAI 키가 존재하지 않아 종료합니다.")
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
        'YOUTUBE_REFRESH_TOKEN': youtube_creds.get('refresh_token', ''),
    })

    print("=" * 60)
    print(f"✅ 프로젝트: {PROJECT_ID}")
    print(f"🔑 OpenAI 키 로드 완료 (총 {len(openai_keys)}개) → 사용 키 앞 10글자: {openai_api_key[:10]}...")
    print("🎥 API 키 및 인증 정보 환경변수 설정 완료")
    print("=" * 60)

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
        print("✍️ 콘텐츠 생성 완료")

        video_path = create_video(content_text, topic)
        print(f"🎞️ 영상 생성 완료: {video_path}")

        thumbnail_path = generate_thumbnail(topic)
        print(f"🖼️ 썸네일 생성 완료: {thumbnail_path}")

        upload_to_youtube(video_path, thumbnail_path, topic)
        print(f"🚀 유튜브 업로드 완료: {topic}")

if __name__ == "__main__":
    main()
