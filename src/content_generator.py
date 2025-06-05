import os
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import secretmanager
import google.generativeai as genai
import openai
from .utils import get_secret, rotate_api_key

logger = logging.getLogger(__name__)

class YouTubeAutomation:
    def __init__(self):
        self.project_id = os.getenv('GCP_PROJECT_ID')
        self.secret_client = secretmanager.SecretManagerServiceClient()
        
        # GCP 서비스 계정 키 로드
        sa_key = json.loads(get_secret("GCP_SERVICE_ACCOUNT_KEY"))
        self.credentials = service_account.Credentials.from_service_account_info(
            sa_key, scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        
        # YouTube API 클라이언트
        youtube_api_key = get_secret("YOUTUBE_CREDENTIALS")
        self.youtube = build("youtube", "v3", credentials=self.credentials, developerKey=youtube_api_key)

    def generate_content(self, topic):
        """AI를 이용한 콘텐츠 생성 (최적화된 프롬프트)"""
        selected_ai = rotate_api_key()
        content = {
            "title": f"{topic} 초고속 분석",
            "title_text": f"{topic}🔥",  # 썸네일용
            "script": "",
            "description": f"{topic}에 대한 최신 정보! AI 자동 생성 콘텐츠입니다. 구독과 좋아요 부탁드려요!"
        }

        try:
            # 최적화된 프롬프트
            prompt = f"""
[ROLE]
너는 유튜브 조회수 100만 달성 전문가야. 지금부터 {topic} 주제로 15초 쇼츠 영상을 만들거야.

[REQUIREMENTS]
1. 첫 3초: 충격적인 사실로 시선 강탈
2. 중간: 핵심 정보 2-3개
3. 마지막: 호기심 유발 질문
4. 전체: 이모지 3개 이상 사용
5. 문장당 5단어 이내

[EXAMPLE]
🚨AI가 인간을 대체한다? 
🤖 2025년 현재 47% 직업 위험 
💡재교육 필수! 
⚠️당신의 미래는?

[OUTPUT]
스크립트만 출력!
"""
            if "GEMINI_API_KEY" in selected_ai:
                genai.configure(api_key=selected_ai["GEMINI_API_KEY"])
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                content["script"] = response.text.strip()
                
                # 제목 생성
                title_prompt = f"위 내용을 바탕으로 15자 이내의 자극적인 제목 생성 (이모지 포함)"
                title_response = model.generate_content(title_prompt)
                content["title"] = title_response.text.strip()
                
            elif "OPENAI_API_KEY" in selected_ai:
                client = openai.OpenAI(api_key=selected_ai["OPENAI_API_KEY"])
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150
                )
                content["script"] = response.choices[0].message.content.strip()
                
                # 제목 생성
                title_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "위 내용을 바탕으로 15자 이내의 자극적인 제목 생성 (이모지 포함)"}],
                    max_tokens=50
                )
                content["title"] = title_response.choices[0].message.content.strip()
            
            logger.info(f"✅ AI 콘텐츠 생성 완료: {content['title']}")
            return content
            
        except Exception as e:
            logger.error(f"❌ AI 콘텐츠 생성 실패: {str(e)}")
            # 기본 콘텐츠로 대체
            content["script"] = f"{topic}에 대한 최신 정보! 놀라운 사실들을 확인해보세요."
            return content
