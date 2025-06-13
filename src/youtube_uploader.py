# src/youtube_uploader.py (전체 코드)

import os
import json
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

# 이 스코프는 유튜브에 동영상을 업로드할 수 있는 권한을 의미합니다.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    """
    GitHub Secrets에 저장된 인증 정보(token.json)를 사용하여 유튜브 API 서비스 객체를 생성합니다.
    """
    creds_json_str = os.getenv("YOUTUBE_OAUTH_CREDENTIALS")
    if not creds_json_str:
        logger.error("❌ YOUTUBE_OAUTH_CREDENTIALS 환경변수가 없습니다.")
        return None

    try:
        # JSON 문자열을 파이썬 딕셔너리로 변환
        creds_info = json.loads(creds_json_str)
        # 딕셔너리 정보로 Credentials 객체 생성
        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)
        
        # 토큰이 유효한지, 만료되었다면 갱신 가능한지 확인
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # 로컬에서는 자동으로 갱신되지만, 서버 환경에서는 이 과정이 복잡할 수 있습니다.
                # token.json을 주기적으로 갱신해주는 것이 가장 확실합니다.
                logger.warning("⚠️ 유튜브 인증 토큰이 만료되었을 수 있습니다. 갱신이 필요합니다.")
            else:
                logger.error("❌ 유효한 유튜브 인증 정보를 찾을 수 없습니다. 로컬에서 'authorize.py'를 다시 실행하여 token.json을 갱신하고, 그 내용을 GitHub Secret에 업데이트하세요.")
                return None
        
        return build('youtube', 'v3', credentials=creds)

    except Exception as e:
        logger.error(f"❌ 유튜브 인증 서비스 생성 중 오류 발생: {str(e)}")
        return None

def upload_video(video_path: str, title: str, description: str, tags: list, category_id: str = "28"):
    """
    주어진 경로의 동영상을 유튜브에 업로드합니다.
    """
    try:
        youtube = get_authenticated_service()
        if not youtube:
            logger.error("유튜브 인증에 실패하여 업로드를 중단합니다.")
            return

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id # 28: 과학 기술, 22: 사람/블로그, 27: 교육 등
            },
            "status": {
                "privacyStatus": "private" # private: 비공개, public: 공개, unlisted: 일부 공개
            }
        }

        logger.info(f"🚀 '{title}' 영상의 유튜브 업로드를 시작합니다...")
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = request.execute()
        logger.info(f"✅ 유튜브 업로드 성공! 비디오 ID: {response.get('id')}")

    except Exception as e:
        logger.error(f"❌ 유튜브 업로드 중 심각한 오류 발생: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
