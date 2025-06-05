import os
import json
import logging
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import secretmanager
import google.generativeai as genai # Google Gemini API
import openai # OpenAI API
from .utils import get_secret, rotate_api_key # utils에서 get_secret와 rotate_api_key 임포트

logger = logging.getLogger(__name__)

class YouTubeAutomation:
    def __init__(self):
        self.project_id = os.getenv('GCP_PROJECT_ID')
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID 환경 변수 미설정")
        
        # Secret Manager 클라이언트 초기화
        self.secret_client = secretmanager.SecretManagerServiceClient()
        
        # GCP 서비스 계정 키 동적 로드 (GCP API 접근용)
        try:
            sa_key = self._get_secret("GCP_SERVICE_ACCOUNT_KEY")
            self.credentials = service_account.Credentials.from_service_account_info(
                json.loads(sa_key),
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            # 환경 변수에서 GOOGLE_APPLICATION_CREDENTIALS 제거 (Secret Manager 사용)
            if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
                del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        except Exception as e:
            logger.error(f"GCP 서비스 계정 키 로드 실패: {e}")
            raise

        # OpenAI 및 Gemini API 키는 필요 시 rotate_api_key를 통해 동적으로 가져옴
        # YouTube API 클라이언트 생성 (개발자 키는 Secret Manager에서 가져옴)
        try:
            youtube_api_key = self._get_secret("YOUTUBE_CREDENTIALS") # 이 키는 YouTube Data API 호출에 사용
            self.youtube = build("youtube", "v3", credentials=self.credentials, developerKey=youtube_api_key)
        except Exception as e:
            logger.error(f"YouTube API 클라이언트 초기화 실패: {e}")
            raise

    def _get_secret(self, secret_id):
        """Secret Manager에서 비밀 값 가져오기"""
        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
            response = self.secret_client.access_secret_version(name=name)
            return response.payload.data.decode('UTF-8')
        except Exception as e:
            logger.error(f"Secret Manager에서 '{secret_id}' 비밀 값 가져오기 실패: {e}")
            raise

    def generate_content(self, topic):
        """
        주어진 주제로 유튜브 영상 콘텐츠 (제목, 스크립트, 설명)를 AI로 생성합니다.
        GPT-4o와 Google Gemini를 번갈아 사용합니다.
        """
        selected_ai = rotate_api_key() # utils.py에서 AI 선택 및 API 키 반환
        content = {
            "title": f"{topic} 최신 분석 및 예측",
            "title_text": f"{topic} 핫이슈!", # 썸네일용 간결한 제목
            "script": "",
            "description": f"안녕하세요! 오늘은 '{topic}'에 대해 자세히 알아보는 시간을 갖겠습니다. 이 영상은 최신 AI 기술을 활용하여 자동으로 생성되었습니다. 구독과 좋아요는 저에게 큰 힘이 됩니다!\n\n관련 키워드: #{topic.replace(' ', '')} #AI자동화 #트렌드분석 #Shorts #수익창출",
        }

        try:
            if "GEMINI_API_KEY" in selected_ai: # Gemini API 사용
                genai.configure(api_key=selected_ai["GEMINI_API_KEY"])
                model = genai.GenerativeModel('gemini-pro')
                prompt = f"당신은 유튜브 콘텐츠 전문가입니다. '{topic}' 주제로 10초 내외의 유튜브 쇼츠 영상 스크립트를 작성해주세요. 주요 내용과 핵심 메시지를 간결하게 담아주세요. 시작과 끝 인사 없이 바로 내용부터 시작하고, 각 문장을 짧게 끊어주세요. 예시: '최신 AI 기술의 등장!', '삶을 어떻게 변화시킬까요?', '놀라운 속도와 정확성!'\n\n스크립트:"
                response = model.generate_content(prompt)
                script = response.text.strip()
                logger.info(f"✨ Gemini API로 스크립트 생성 완료. 길이: {len(script)}자")
                content["script"] = script

                # 제목과 설명도 Gemini로 생성 (선택 사항)
                title_prompt = f"'{topic}' 주제로 유튜브 쇼츠 영상의 자극적이고 클릭 유도적인 제목을 20자 이내로 1개만 제안해주세요. 이모티콘을 사용해도 좋습니다. 예시: '💥AI 대폭발! 당신의 미래는?🤔'"
                title_response = model.generate_content(title_prompt)
                title = title_response.text.strip().replace("제목: ", "").replace("```", "").replace("json", "")
                content["title"] = title if title else content["title"]
                content["title_text"] = title if title else content["title_text"] # 썸네일용 제목도 업데이트

                description_prompt = f"'{topic}' 주제로 유튜브 쇼츠 영상의 설명을 150자 이내로 작성해주세요. 핵심 내용을 요약하고 관련 해시태그를 포함해주세요. 영상이 AI 자동 생성되었음을 명시해주세요."
                description_response = model.generate_content(description_prompt)
                description = description_response.text.strip().replace("설명: ", "").replace("```", "").replace("json", "")
                content["description"] = description if description else content["description"]


            elif "OPENAI_API_KEY" in selected_ai: # OpenAI API 사용
                client = openai.OpenAI(api_key=selected_ai["OPENAI_API_KEY"])
                prompt = f"당신은 유튜브 콘텐츠 전문가입니다. '{topic}' 주제로 10초 내외의 유튜브 쇼츠 영상 스크립트를 작성해주세요. 주요 내용과 핵심 메시지를 간결하게 담아주세요. 시작과 끝 인사 없이 바로 내용부터 시작하고, 각 문장을 짧게 끊어주세요. 예시: '최신 AI 기술의 등장!', '삶을 어떻게 변화시킬까요?', '놀라운 속도와 정확성!'\n\n스크립트:"
                response = client.chat.completions.create(
                    model="gpt-4o", # GPT-4o 사용
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                    temperature=0.7,
                )
                script = response.choices[0].message.content.strip()
                logger.info(f"✨ OpenAI API로 스크립트 생성 완료. 길이: {len(script)}자")
                content["script"] = script

                # 제목과 설명도 OpenAI로 생성
                title_prompt = f"'{topic}' 주제로 유튜브 쇼츠 영상의 자극적이고 클릭 유도적인 제목을 20자 이내로 1개만 제안해주세요. 이모티콘을 사용해도 좋습니다. 예시: '💥AI 대폭발! 당신의 미래는?🤔'"
                title_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": title_prompt}],
                    max_tokens=50,
                    temperature=0.7,
                )
                title = title_response.choices[0].message.content.strip().replace("제목: ", "")
                content["title"] = title if title else content["title"]
                content["title_text"] = title if title else content["title_text"] # 썸네일용 제목도 업데이트

                description_prompt = f"'{topic}' 주제로 유튜브 쇼츠 영상의 설명을 150자 이내로 작성해주세요. 핵심 내용을 요약하고 관련 해시태그를 포함해주세요. 영상이 AI 자동 생성되었음을 명시해주세요."
                description_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": description_prompt}],
                    max_tokens=200,
                    temperature=0.7,
                )
                description = description_response.choices[0].message.content.strip().replace("설명: ", "")
                content["description"] = description if description else content["description"]

            else:
                logger.warning("⚠️ 유효한 AI API 키가 선택되지 않았습니다. 기본 콘텐츠로 진행합니다.")

        except Exception as e:
            logger.error(f"🔴 AI 콘텐츠 생성 실패: {str(e)}\n{traceback.format_exc()}")
            logger.warning("⚠️ AI 콘텐츠 생성 실패로 기본 콘텐츠로 진행합니다.")
            # 실패 시에도 기본 콘텐츠로 진행하여 전체 흐름 끊기지 않도록
            content["script"] = f"오늘의 주제는 {topic} 입니다. 자세한 내용을 알아봅시다. AI가 알려주는 최신 정보에 집중해주세요!"
            content["description"] = f"AI 자동 생성 콘텐츠: {topic}에 대한 간략한 정보입니다."

        logger.info(f"콘텐츠 최종 생성 완료: {content['title']}")
        return content

    # 기존 should_run_now, get_trending_topic, create_video, upload_to_youtube는 app.py와
    # 다른 src 모듈로 이동되었거나 대체되었습니다.
    # 이 클래스는 오직 콘텐츠 생성 역할만 담당합니다.
