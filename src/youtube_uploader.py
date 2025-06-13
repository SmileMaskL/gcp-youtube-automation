# src/youtube_uploader.py (전체 코드)

import os
import json
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    creds_json_str = os.getenv("YOUTUBE_OAUTH_CREDENTIALS")
    if not creds_json_str:
        logger.error("❌ YOUTUBE_OAUTH_CREDENTIALS 환경변수가 없습니다.")
        return None

    try:
        creds_info = json.loads(creds_json_str)
        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.warning("⚠️ 유튜브 인증 토큰이 만료되었을 수 있습니다. 갱신이 필요합니다.")
            else:
                logger.error("❌ 유효한 유튜브 인증 정보를 찾을 수 없습니다. 로컬에서 'authorize.py'를 다시 실행하여 token.json을 갱신하세요.")
                return None
        
        return build('youtube', 'v3', credentials=creds)

    except Exception as e:
        logger.error(f"❌ 유튜브 인증 서비스 생성 중 오류 발생: {str(e)}")
        return None

# 🔥 함수에 '재생목록 ID', '공개 상태'를 설정하는 기능을 추가했습니다!
def upload_video(video_path: str, title: str, description: str, tags: list, 
                 playlist_id: str = None, 
                 privacy_status: str = "private", 
                 category_id: str = "28"):
    try:
        youtube = get_authenticated_service()
        if not youtube:
            logger.error("유튜브 인증에 실패하여 업로드를 중단합니다.")
            return

        # 🔥 업로드할 영상의 세부 정보를 설정하는 부분입니다.
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id # 28: 과학/기술
            },
            "status": {
                "privacyStatus": privacy_status, # 🔥 '비공개' 대신 '공개(public)'로 설정 가능
                "selfDeclaredMadeForKids": False # 🔥 '아니요, 아동용이 아닙니다' 자동 설정!
            }
        }

        # 🔥 재생목록 ID가 있다면, 요청 본문에 추가합니다.
        if playlist_id:
            body["snippet"]["playlistIds"] = [playlist_id]
            logger.info(f"지정된 재생목록({playlist_id})에 추가합니다.")

        logger.info(f"🚀 '{title}' 영상의 유튜브 업로드를 시작합니다... (상태: {privacy_status})")
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
