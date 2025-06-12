import os
import random
from google.oauth2 import service_account
from google.cloud import secretmanager
from datetime import datetime, timedelta

class APIKeyManager:
    def __init__(self, project_id):
        # 서비스 계정 인증 설정
        credentials = service_account.Credentials.from_service_account_file(
            'gcp-service-key.json',
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # Secret Manager 클라이언트 초기화
        self.client = secretmanager.SecretManagerServiceClient(credentials=credentials)
        self.project_id = project_id
        
    def get_openai_api_key(self):
        # OpenAI API 키를 로테이션으로 가져오기
        secret_name = f"projects/{self.project_id}/secrets/openai-api-keys/versions/latest"
        response = self.client.access_secret_version(request={"name": secret_name})
        return response.payload.data.decode("UTF-8")
    
    def get_other_api_keys(self):
        # 다른 API 키들을 가져오기
        api_keys = {}
        
        # Gemini API 키
        secret_name = f"projects/{self.project_id}/secrets/gemini-api-key/versions/latest"
        response = self.client.access_secret_version(request={"name": secret_name})
        api_keys['gemini'] = response.payload.data.decode("UTF-8")
        
        # ElevenLabs API 키
        secret_name = f"projects/{self.project_id}/secrets/elevenlabs-api-key/versions/latest"
        response = self.client.access_secret_version(request={"name": secret_name})
        api_keys['elevenlabs'] = response.payload.data.decode("UTF-8")
        
        # YouTube OAuth 자격증명
        secret_name = f"projects/{self.project_id}/secrets/youtube-oauth-credentials/versions/latest"
        response = self.client.access_secret_version(request={"name": secret_name})
        api_keys['youtube'] = response.payload.data.decode("UTF-8")
        
        return api_keys

def main():
    # API 키 관리자 초기화
    project_id = os.environ.get('GCP_PROJECT_ID')
    api_manager = APIKeyManager(project_id)
    
    # OpenAI API 키 가져오기
    openai_key = api_manager.get_openai_api_key()
    
    # 다른 API 키들 가져오기
    other_keys = api_manager.get_other_api_keys()
    
    # 환경변수로 설정
    os.environ['OPENAI_API_KEY'] = openai_key
    os.environ['GEMINI_API_KEY'] = other_keys['gemini']
    os.environ['ELEVENLABS_API_KEY'] = other_keys['elevenlabs']
    os.environ['YOUTUBE_CREDENTIALS'] = other_keys['youtube']
    
    # GitHub Secrets 설정
    os.environ['GCP_PROJECT_ID'] = os.environ.get('GCP_PROJECT_ID')
    os.environ['GCP_SA_KEY'] = os.environ.get('GCP_SA_KEY')
    os.environ['GCP_SERVICE_ACCOUNT'] = os.environ.get('GCP_SERVICE_ACCOUNT')
    os.environ['GCP_WORKLOAD_IDENTITY_PROVIDER'] = os.environ.get('GCP_WORKLOAD_IDENTITY_PROVIDER')
    
    # 여기서부터는 원래 코드와 동일하게 실행
    print("모든 API 키들이 환경변수로 설정되었습니다.")

if __name__ == "__main__":
    main()
