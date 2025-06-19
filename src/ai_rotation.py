import os
import json
import logging
import random
from typing import List, Optional, Dict
from google.cloud import secretmanager
from src.openai_utils import OpenAIClient
from src.gemini_utils import GeminiClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIRotation:
    """단순한 키 순환 클래스 (OpenAI용)"""
    def __init__(self, keys: List[str]):
        if not keys:
            raise ValueError("OpenAI 키 리스트가 비어 있습니다.")
        self.keys = keys
        self.index = 0

    def get_next_key(self) -> str:
        key = self.keys[self.index]
        self.index = (self.index + 1) % len(self.keys)
        return key


class AIClientRotator:
    def __init__(self):
        self.clients = self._initialize_clients()
        self.current_index = 0

    def _initialize_clients(self) -> List[Dict]:
        """사용 가능한 AI 클라이언트 초기화"""
        clients = []

        # 🔁 OpenAI 키 로테이션 초기화
        openai_keys = self._get_openai_keys()
        self.openai_rotator = AIRotation(openai_keys)

        for _ in openai_keys:
            clients.append({
                'type': 'openai',
                'client': OpenAIClient(api_key=self.openai_rotator.get_next_key()),
                'weight': 0.7
            })

        # Gemini 클라이언트 추가
        gemini_key = self._get_gemini_key()
        if gemini_key:
            clients.append({
                'type': 'gemini',
                'client': GeminiClient(api_key=gemini_key),
                'weight': 0.3
            })

        return clients

    def _get_openai_keys(self) -> List[str]:
        """OpenAI API 키 목록 가져오기 (GCP or 환경변수)"""
        try:
            client = secretmanager.SecretManagerServiceClient()
            secret_name = f"projects/{os.getenv('GCP_PROJECT_ID')}/secrets/openai-api-keys/versions/latest"
            response = client.access_secret_version(name=secret_name)
            keys = response.payload.data.decode("UTF-8").split(',')
            return [key.strip() for key in keys if key.strip()]
        except Exception as e:
            logger.warning(f"OpenAI 키 가져오기 실패(GCP): {e}")
            env_keys = os.getenv("OPENAI_API_KEYS", "")
            return [key.strip() for key in env_keys.split(',') if key.strip()]

    def _get_gemini_key(self) -> Optional[str]:
        """Gemini API 키 가져오기 (GCP or 환경변수)"""
        try:
            client = secretmanager.SecretManagerServiceClient()
            secret_name = f"projects/{os.getenv('GCP_PROJECT_ID')}/secrets/gemini-api-key/versions/latest"
            response = client.access_secret_version(name=secret_name)
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.warning(f"Gemini 키 가져오기 실패(GCP): {e}")
            return os.getenv("GEMINI_API_KEY")

    def generate_content(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """AI 로테이션으로 콘텐츠 생성"""
        for _ in range(max_retries):
            client_info = self._select_client()
            try:
                if client_info['type'] == 'openai':
                    content = client_info['client'].generate_content(
                        prompt,
                        model="gpt-4o"
                    )
                else:
                    content = client_info['client'].generate_content(prompt)

                if content:
                    return content
            except Exception as e:
                logger.error(f"{client_info['type']} 생성 실패: {e}")
                continue

        return None

    def _select_client(self) -> Dict:
        """가중치 기반 클라이언트 선택"""
        total_weight = sum(client['weight'] for client in self.clients)
        rand = random.uniform(0, total_weight)

        cumulative = 0
        for client in self.clients:
            cumulative += client['weight']
            if rand <= cumulative:
                return client

        return self.clients[0]
