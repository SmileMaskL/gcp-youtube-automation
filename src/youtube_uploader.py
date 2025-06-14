import os
import json
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pathlib import Path

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    try:
        creds_json_str = os.getenv("YOUTUBE_OAUTH_CREDENTIALS")
        if not creds_json_str:
            raise ValueError("YOUTUBE_OAUTH_CREDENTIALS 환경변수가 없습니다.")
        
        creds_info = json.loads(creds_json_str)
        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(None)
            else:
                raise ValueError("유효한 인증 정보가 없습니다.")

        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"인증 서비스 생성 실패: {str(e)}")
        return None

def upload_video(video_path: str, title: str, description: str, tags: list,
                 privacy_status: str = "private", category_id: str = "28",
                 thumbnail_path: str = None) -> bool:
    try:
        youtube = get_authenticated_service()
        if not youtube:
            return False

        # 영상 업로드
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )
        response = request.execute()
        video_id = response.get('id')

        # 썸네일 업로드
        if thumbnail_path and video_id:
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                logger.info(f"썸네일 업로드 성공: {thumbnail_path}")
            except Exception as e:
                logger.warning(f"썸네일 업로드 실패: {str(e)}")

        logger.info(f"업로드 완료! 비디오 ID: {video_id}")
        return True

    except Exception as e:
        logger.error(f"업로드 중 오류 발생: {str(e)}")
        return False
