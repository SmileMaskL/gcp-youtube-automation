import os
import json
import random
from google.cloud import secretmanager
from src.content_generator import generate_content
from src.video_creator import create_video
from src.thumbnail_generator import generate_thumbnail
from src.youtube_uploader import upload_to_youtube

class APIKeyManager:
    def __init__(self, project_id="youtube-fully-automated"):
        """
        GCP Secret Manager에서 API 키들을 불러오는 클래스
        """
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id
        
    def get_secret(self, secret_id):
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
        response = self.client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    
    def get_openai_keys(self):
        """
        OpenAI API 키 여러 개를 JSON 배열 형태로 받아서 리스트로 반환
        """
        json_str = self.get_secret("openai-api-keys")
        try:
            keys = json.loads(json_str)
            if not isinstance(keys, list):
                raise ValueError("OpenAI keys secret must be a JSON array.")
            return keys
        except Exception as e:
            print(f"❌ OpenAI API 키 JSON 파싱 오류: {e}")
            return []
    
    def get_other_api_keys(self):
        """
        기타 API 키들을 딕셔너리로 반환
        """
        api_keys = {}
        secrets_mapping = {
            'gemini': 'gemini-api-key',
            'elevenlabs': 'elevenlabs-api-key',
            'pexels': 'pexels-api-key',
            'youtube': 'youtube-oauth-credentials'
        }
        for key_type, secret_name in secrets_mapping.items():
            try:
                api_keys[key_type] = self.get_secret(secret_name)
            except Exception as e:
                print(f"❌ {key_type} 키 불러오기 실패: {e}")
                api_keys[key_type] = ""
        return api_keys

def parse_youtube_credentials(credentials_str):
    try:
        return json.loads(credentials_str)
    except json.JSONDecodeError:
        # 환경변수 기반 포맷 지원
        return {
            "client_id": os.getenv("YOUTUBE_CLIENT_ID", ""),
            "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET", ""),
            "refresh_token": os.getenv("YOUTUBE_REFRESH_TOKEN", "")
        }

def main():
    PROJECT_ID = "youtube-fully-automated"
    api_manager = APIKeyManager(PROJECT_ID)
    
    # OpenAI 키 여러 개 로드
    openai_keys = api_manager.get_openai_keys()
    if not openai_keys:
        print("⚠️ OpenAI API 키가 없습니다. 종료합니다.")
        return
    
    # 다른 API 키들도 로드
    other_keys = api_manager.get_other_api_keys()
    
    # YouTube 인증 정보 파싱
    youtube_creds = parse_youtube_credentials(other_keys.get('youtube', '{}'))
    
    # OpenAI 키 무작위 선택 (로테이션 효과)
    openai_api_key = random.choice(openai_keys)
    
    # 환경변수에 설정 (외부 라이브러리들이 이 키를 사용하도록)
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
    print(f"✅ GCP 프로젝트: {PROJECT_ID}")
    print(f"🔑 선택된 OpenAI API 키: {openai_api_key[:10]}... (총 {len(openai_keys)}개 중 1개 사용)")
    print(f"🎥 기타 API 키 및 YouTube 인증 정보 세팅 완료")
    print("="*50)
    
    # 콘텐츠 주제 예시 (실제 비즈니스에 맞게 바꾸세요)
    topics = [
        "GCP로 유튜브 자동화 마스터하기",
        "AI로 월 1000만원 버는 방법",
        "ChatGPT 5.0 실전 활용법",
        "구글 제미니 고급 프로덕트 리뷰",
        "무료 클라우드로 수익 창출"
    ]
    
    for i, topic in enumerate(topics):
        print(f"\n🎬 [{i+1}/{len(topics)}] 주제: {topic}")
        
        # 콘텐츠 텍스트 생성
        content_text = generate_content(topic)
        print(f"✍️ 콘텐츠 생성 완료")
        
        # 영상 생성
        video_path = create_video(content_text, topic)
        print(f"🎞️ 영상 생성 완료: {video_path}")
        
        # 썸네일 생성
        thumbnail_path = generate_thumbnail(topic)
        print(f"🖼️ 썸네일 생성 완료: {thumbnail_path}")
        
        # 유튜브 업로드
        upload_to_youtube(video_path, thumbnail_path, topic)
        print(f"🚀 유튜브 업로드 완료: {topic}")
        
        # 다음 영상까지 딜레이 (필요시)
        # time.sleep(5)

if __name__ == "__main__":
    main()
