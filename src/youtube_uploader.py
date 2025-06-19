import os
import json
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from src.config import Config

logger = logging.getLogger(__name__)

# YouTube API 스코프 (업로드 권한)
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    creds = None
    # YOUTUBE_OAUTH_CREDENTIALS는 refresh_token, client_id, client_secret을 포함하는 JSON 문자열입니다.
    # 이 JSON은 GitHub Secrets에 저장되어 있어야 합니다.
    # 예시: {"refresh_token": "...", "client_id": "...", "client_secret": "..."}
    
    try:
        creds_data = Config.get_youtube_oauth_credentials()
        
        # refresh_token을 사용하여 새로운 액세스 토큰을 발급받습니다.
        # InstalledAppFlow를 통해 초기 인증 과정을 거쳐야 refresh_token을 얻을 수 있습니다.
        # GitHub Actions에서는 대화형 인증이 불가능하므로, 미리 생성된 refresh_token을 사용합니다.
        creds = Credentials.from_authorized_user_info(
            info={
                'refresh_token': creds_data['refresh_token'],
                'client_id': creds_data['client_id'],
                'client_secret': creds_data['client_secret']
            },
            scopes=SCOPES
        )
        
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                logger.info("Access token expired, refreshing...")
                creds.refresh(Request())
            else:
                raise ValueError("Invalid or expired credentials without refresh token.")
        
        logger.info("YouTube API 서비스 인증 성공.")
        return build('youtube', 'v3', credentials=creds)

    except Exception as e:
        logger.error(f"YouTube API 서비스 인증 실패: {e}")
        logger.error("YOUTUBE_OAUTH_CREDENTIALS가 올바르게 설정되었는지 확인하십시오.")
        logger.error("Refresh Token을 얻기 위한 초기 OAuth 인증 과정이 필요합니다.")
        raise

def upload_youtube_short(file_path: str, title: str, description: str, tags: list, category_id: str, privacy_status: str, thumbnail_path: Optional[str] = None) -> bool:
    """
    YouTube Shorts 영상을 업로드합니다.
    Args:
        file_path: 업로드할 비디오 파일 경로.
        title: 비디오 제목.
        description: 비디오 설명.
        tags: 비디오 태그 목록.
        category_id: 비디오 카테고리 ID (예: "22" for People & Blogs).
        privacy_status: "public", "private", 또는 "unlisted".
        thumbnail_path: 썸네일 이미지 파일 경로 (선택 사항).
    Returns:
        업로드 성공 여부 (True/False).
    """
    try:
        youtube = get_authenticated_service()
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': category_id,
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False # YouTube 키즈 채널이 아니라면 False
            },
            'kind': 'youtube#video'
        }

        # MediaFileUpload를 사용하여 비디오 업로드
        media_body = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        logger.info(f"유튜브 쇼츠 업로드 시작: {title}")
        insert_request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media_body
        )

        response = None
        while response is None:
            status, response = insert_request.next_chunk()
            if status:
                logger.info(f"Uploaded {int(status.progress() * 100)}% of {title}")

        if response is not None:
            logger.info(f"유튜브 업로드 완료. 비디오 ID: {response['id']}")
            
            # 썸네일 업로드
            if thumbnail_path and os.path.exists(thumbnail_path):
                logger.info(f"썸네일 업로드 시작: {thumbnail_path}")
                thumbnail_media = MediaFileUpload(thumbnail_path, mimetype='image/png')
                try:
                    youtube.thumbnails().set(
                        videoId=response['id'],
                        media_body=thumbnail_media
                    ).execute()
                    logger.info(f"썸네일 업로드 완료 for video ID: {response['id']}")
                except HttpError as e:
                    logger.error(f"썸네일 업로드 중 오류 발생 (HTTP Error): {e}")
                    # API 할당량 초과 시 여기서 오류 발생 가능
                    if e.resp.status == 403:
                        logger.error("YouTube API 할당량 초과 또는 권한 부족으로 썸네일 업로드 실패.")
                except Exception as e:
                    logger.error(f"썸네일 업로드 중 예상치 못한 오류 발생: {e}")
            else:
                logger.warning("썸네일 파일이 없거나 유효하지 않아 썸네일을 업로드하지 않습니다.")
            
            return True
        else:
            logger.error(f"유튜브 업로드 실패: {title} (응답 없음)")
            return False

    except HttpError as e:
        logger.error(f"YouTube API 오류 (HTTP Error): {e}")
        # API 할당량 관련 오류 메시지 확인
        if e.resp.status == 403 and "quota" in str(e).lower():
            logger.error("YouTube API 할당량 초과로 업로드 실패. 다음 실행을 기다리십시오.")
        return False
    except Exception as e:
        logger.error(f"유튜브 업로드 중 예상치 못한 오류 발생: {e}", exc_info=True)
        return False
