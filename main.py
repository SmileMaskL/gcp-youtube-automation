import os
import json
import time
from google.cloud import secretmanager
from src.content_generator import generate_content
from src.video_creator import create_video
from src.thumbnail_generator import generate_thumbnail
from src.youtube_uploader import upload_to_youtube

class APIKeyManager:
    def __init__(self, project_id="youtube-fully-automated"):
        """
        Workload Identity 기반 GCP 시크릿 매니저 초기화
        - GitHub Actions 환경에서 자동 인증
        """
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id
        
    def get_openai_api_key(self):
        """OpenAI API 키 조회"""
        secret_name = f"projects/{self.project_id}/secrets/openai-api-keys/versions/latest"
        response = self.client.access_secret_version(request={"name": secret_name})
        return response.payload.data.decode("UTF-8")
    
    def get_other_api_keys(self):
        """모든 필수 API 키 일괄 조회"""
        api_keys = {}
        secrets_mapping = {
            'gemini': 'gemini-api-key',
            'elevenlabs': 'elevenlabs-api-key',
            'pexels': 'pexels-api-key',
            'youtube': 'youtube-oauth-credentials'  # 통합 YouTube 인증 정보
        }
        
        for key_type, secret_name in secrets_mapping.items():
            full_path = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = self.client.access_secret_version(request={"name": full_path})
            api_keys[key_type] = response.payload.data.decode("UTF-8")
        
        return api_keys

def parse_youtube_credentials(credentials_str):
    """YouTube 통합 인증 정보 파싱"""
    try:
        return json.loads(credentials_str)
    except json.JSONDecodeError:
        # Fallback: 사용자의 기존 포맷 지원
        return {
            "client_id": os.getenv("YOUTUBE_CLIENT_ID", ""),
            "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET", ""),
            "refresh_token": os.getenv("YOUTUBE_REFRESH_TOKEN", "")
        }

def main():
    # 프로젝트 ID 설정 (사용자 고정값)
    PROJECT_ID = "youtube-fully-automated"
    
    # API 매니저 초기화
    api_manager = APIKeyManager(PROJECT_ID)
    
    # API 키 로드
    openai_key = api_manager.get_openai_api_key()
    other_keys = api_manager.get_other_api_keys()
    
    # YouTube 인증 정보 파싱
    youtube_creds = parse_youtube_credentials(other_keys['youtube'])
    
    # 환경변수 설정
    os.environ.update({
        'GCP_PROJECT_ID': PROJECT_ID,
        'OPENAI_API_KEY': openai_key,
        'GEMINI_API_KEY': other_keys['gemini'],
        'ELEVENLABS_API_KEY': other_keys['elevenlabs'],
        'PEXELS_API_KEY': other_keys['pexels'],
        'YOUTUBE_CLIENT_ID': youtube_creds.get('client_id', ''),
        'YOUTUBE_CLIENT_SECRET': youtube_creds.get('client_secret', ''),
        'YOUTUBE_REFRESH_TOKEN': youtube_creds.get('refresh_token', '')
    })
    
    print("="*50)
    print(f"✅ GCP 프로젝트 설정: {PROJECT_ID}")
    print(f"🔑 로드된 API 키: OpenAI, Gemini, ElevenLabs, Pexels, YouTube")
    print("="*50)
    
    # 수익화 가능 주제 리스트 (2025년 검증)
    monetizable_topics = [
        "GCP로 유튜브 자동화 마스터하기",
        "AI로 월 1000만원 버는 방법",
        "ChatGPT 5.0 실전 활용법",
        "구글 제미니 고급 프로덕트 리뷰",
        "무료 클라우드로 수익 창출"
    ]
    
    # 영상 생성 파이프라인 실행
    for i, topic in enumerate(monetizable_topics):
        print(f"\n🚀 [{i+1}/{len(monetizable_topics)}] 영상 생성 시작: '{topic}'")
        
        try:
            # 콘텐츠 생성
            content = generate_content(topic)
            print(f"📝 콘텐츠 생성 완료: {content[:50]}...")
            
            # 영상 제작
            video_path = create_video(content, topic)
            print(f"🎬 영상 제작 완료: {video_path}")
            
            # 썸네일 생성
            thumbnail_path = generate_thumbnail(topic)
            print(f"🖼 썸네일 생성 완료: {thumbnail_path}")
            
            # YouTube 업로드
            video_id = upload_to_youtube(
                video_path,
                thumbnail_path,
                title=topic,
                description="AI로 자동 생성된 수익화 콘텐츠"
            )
            print(f"📤 업로드 성공: https://youtu.be/{video_id}")
            
        except Exception as e:
            print(f"❌ 에러 발생: {str(e)}")
        
        # API 한도 회피 대기 (마지막 주제 제외)
        if i < len(monetizable_topics) - 1:
            wait_time = 300  # 5분
            print(f"⏱ 다음 작업 전 {wait_time}초 대기...")
            time.sleep(wait_time)

if __name__ == "__main__":
    main()
