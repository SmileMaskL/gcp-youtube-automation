import os
import io
import json
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

# YouTube API 스코프
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube" # 기본 스코프 추가
]

def get_authenticated_service(credentials_json_str: str):
    """
    YouTube API 서비스 객체를 인증하여 반환합니다.
    Args:
        credentials_json_str (str): GitHub Secret에서 가져온 OAuth 2.0 클라이언트 ID JSON 문자열.
    Returns:
        googleapiclient.discovery.Resource: 인증된 YouTube API 서비스 객체.
    """
    creds = None
    token_path = "token.json" # 임시 토큰 파일 경로 (Cloud Run Job이 종료되면 사라짐)

    # 이전에 저장된 토큰이 있는지 확인
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            logger.info("Loaded credentials from token.json")
        except Exception as e:
            logger.warning(f"Could not load credentials from token.json: {e}. Re-authenticating.")
            creds = None

    # 토큰이 유효하지 않거나 만료된 경우 새로고침
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired YouTube OAuth token...")
            try:
                creds.refresh(Request())
                logger.info("YouTube OAuth token refreshed.")
            except Exception as e:
                logger.error(f"Failed to refresh YouTube token: {e}. Re-authenticating from scratch.")
                creds = None
        
        if not creds: # 새로고침도 실패했거나 토큰이 없는 경우
            logger.info("Performing full YouTube OAuth flow...")
            # GitHub Secret에서 받은 JSON 문자열을 파일처럼 읽기
            client_secrets_info = json.loads(credentials_json_str)
            
            # flow 생성 시 `redirect_uri`를 명시적으로 설정 (데스크톱 앱 유형에 맞게)
            flow = InstalledAppFlow.from_client_config(client_secrets_info, SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            
            # headless 환경에서는 브라우저를 열 수 없으므로 수동 인증 코드를 사용해야 합니다.
            # 이 `run_local_server` 또는 `run_console`은 웹 브라우저를 띄웁니다.
            # Cloud Run Job에서는 이 방식이 직접적으로 작동하지 않습니다.
            # 따라서 'refresh_token'을 사용하여 인증을 유지하는 것이 중요합니다.
            
            # 초기 인증은 로컬 PC에서 한 번 수행하여 refresh_token을 얻어야 합니다.
            # 얻은 refresh_token은 YOUTUBE_OAUTH_CREDENTIALS JSON 안에 포함되어야 합니다.
            # 예시: {"web":{"client_id":"...","client_secret":"...","refresh_token":"..."}}

            # 만약 `credentials_json_str`에 이미 `refresh_token`이 포함되어 있다면,
            # `Credentials.from_authorized_user_info`를 사용하여 직접 생성할 수 있습니다.
            
            if "refresh_token" in client_secrets_info.get("installed", {}) or \
               "refresh_token" in client_secrets_info.get("web", {}):
                logger.info("Found refresh token in provided credentials. Using it directly.")
                creds = Credentials.from_authorized_user_info(client_secrets_info.get("installed", {}) or client_secrets_info.get("web", {}), SCOPES)
                creds.refresh(Request()) # refresh_token으로 토큰 새로고침 시도
            else:
                logger.critical("No refresh token found in YOUTUBE_OAUTH_CREDENTIALS. Initial manual authentication is required or the token is invalid.")
                raise ValueError("YouTube OAuth requires a refresh token for non-interactive environments.")

    if creds and creds.token and creds.refresh_token:
        # 토큰을 token.json 파일에 저장 (다음 실행 시 재사용)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        logger.info(f"Credentials saved to {token_path}")
    else:
        logger.error("Failed to obtain valid YouTube credentials with refresh token.")
        raise ValueError("Invalid YouTube credentials.")

    return build('youtube', 'v3', credentials=creds)

def refresh_youtube_oauth_token(credentials_json_str: str):
    """
    YouTube OAuth 토큰을 새로고침하고 업데이트된 자격증명 JSON을 반환합니다.
    """
    creds = None
    try:
        # GitHub Secret에서 받은 JSON 문자열을 파싱
        client_config = json.loads(credentials_json_str)
        # 클라이언트 설정에서 credential 정보 추출 (web 또는 installed 타입)
        auth_info = client_config.get("web", {}) or client_config.get("installed", {})
        
        # 'token'은 유효기간이 짧으므로, 'refresh_token'이 있다면 그것으로 인증 시도
        if "refresh_token" not in auth_info:
            raise ValueError("No refresh_token found in YOUTUBE_OAUTH_CREDENTIALS. Initial manual authorization is required.")

        # refresh_token으로 Credentials 객체 생성
        creds = Credentials.from_authorized_user_info(auth_info, SCOPES)
        creds.token = auth_info.get("token") # 기존 토큰도 있으면 설정
        creds.refresh_token = auth_info["refresh_token"]
        creds.client_id = auth_info["client_id"]
        creds.client_secret = auth_info["client_secret"]
        
        # 토큰 새로고침
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            logger.info("YouTube OAuth token successfully refreshed.")
        elif not creds.valid:
            # 유효하지 않지만 만료되지 않은 경우 (거의 없음) 또는 refresh_token으로도 안 되는 경우
            raise ValueError("YouTube token is invalid and cannot be refreshed.")
        else:
            logger.info("YouTube OAuth token is still valid. No refresh needed.")

        # 업데이트된 자격증명 반환 (refresh_token이 포함된 JSON 형태)
        updated_creds_info = {
            "web": { # 또는 "installed"
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "refresh_token": creds.refresh_token,
                "token": creds.token,
                "token_uri": creds.token_uri,
                "scopes": creds.scopes,
                "expiry": creds.expiry.isoformat() if creds.expiry else None
            }
        }
        return json.dumps(updated_creds_info) # JSON 문자열로 반환

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing YOUTUBE_OAUTH_CREDENTIALS JSON: {e}")
        raise ValueError("Invalid YOUTUBE_OAUTH_CREDENTIALS format.")
    except Exception as e:
        logger.error(f"Error refreshing YouTube OAuth token: {e}", exc_info=True)
        raise

def upload_video(
    file_path: str,
    title: str,
    description: str,
    tags: list,
    credentials_json_str: str,
    thumbnail_path: str = None
):
    """
    YouTube에 동영상을 업로드합니다.
    Args:
        file_path (str): 업로드할 동영상 파일 경로.
        title (str): 동영상 제목.
        description (str): 동영상 설명.
        tags (list): 동영상 태그 목록.
        credentials_json_str (str): YouTube OAuth 2.0 클라이언트 ID JSON 문자열.
        thumbnail_path (str): 썸네일 이미지 파일 경로 (선택 사항).
    Returns:
        str: 업로드된 동영상의 ID, 또는 None (업로드 실패 시).
    """
    logger.info(f"Attempting to upload video: '{title}' from {file_path}")

    # 인증 서비스 가져오기
    youtube = get_authenticated_service(credentials_json_str)

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            ''categoryId': '22',  # 카테고리 ID (22: 코미디, 24: 엔터테인먼트, 28: 과학기술 등)
            'defaultLanguage': 'ko'
        },
        'status': {
            'privacyStatus': 'public' # public, private, unlisted (공개, 비공개, 미등록)
        },
        'processingStatus': {
            'uploadStatus': 'uploaded' # 업로드 상태를 명시
        }
    }

    # 미디어 파일 업로드 준비
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    try:
        # 업로드 요청
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Uploaded {int(status.progress() * 100)}% of video: {title}")

        video_id = response.get('id')
        logger.info(f"Video '{title}' uploaded successfully! Video ID: {video_id}")

        # 썸네일 업로드
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                thumbnail_media = MediaFileUpload(thumbnail_path, mimetype='image/jpeg', resumable=False)
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=thumbnail_media
                ).execute()
                logger.info(f"Thumbnail uploaded for video ID: {video_id}")
            except HttpError as e:
                logger.warning(f"Could not upload thumbnail: {e.content.decode()}")
                if 'forbidden' in e.content.decode().lower() or 'quota' in e.content.decode().lower():
                    logger.error("Thumbnail upload failed due to permission or quota issues. Check YouTube API settings.")
                else:
                    logger.error("Unknown error during thumbnail upload. See logs above.")
            except Exception as e:
                logger.error(f"An unexpected error occurred during thumbnail upload: {e}")
        else:
            logger.warning("Thumbnail path not provided or file does not exist. Skipping thumbnail upload.")

        return video_id

    except HttpError as e:
        logger.error(f"An HTTP error occurred during video upload: {e.content.decode()}")
        if 'quotaExceeded' in e.content.decode():
            logger.critical("YouTube API Daily Quota Exceeded. Cannot upload more videos today.")
        elif 'authError' in e.content.decode():
            logger.critical("YouTube API Authentication Error. Check YOUTUBE_OAUTH_CREDENTIALS.")
        raise # 재시도를 위해 예외 다시 발생
    except Exception as e:
        logger.error(f"An unexpected error occurred during video upload: {e}", exc_info=True)
        raise
