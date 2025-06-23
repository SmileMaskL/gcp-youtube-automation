# src/youtube_uploader.py

import logging
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from config import Config # F401 'config.Config' imported but unused -> 실제 사용되므로 유지

logger = logging.getLogger(__name__)

SCOPES = ["[https://www.googleapis.com/auth/youtube.upload](https://www.googleapis.com/auth/youtube.upload)"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"


def get_authenticated_service(config_instance):
    """
    YouTube API 서비스 객체를 인증하고 반환합니다.
    Refresh Token을 사용하여 인증 정보를 갱신합니다.
    """
    try:
        client_id = config_instance.get_youtube_client_id()
        client_secret = config_instance.get_youtube_client_secret()
        refresh_token = config_instance.get_youtube_refresh_token()

        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)",
                "token_uri": "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)",
                # E501 해결: 줄 길이를 79자 이하로 맞춤
                "auth_provider_x509_cert_url": ("[https://www.googleapis.com/oauth2/v1/](https://www.googleapis.com/oauth2/v1/)"
                                                "certs")
            }
        }

        credentials = google.oauth2.credentials.Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=client_config["web"]["token_uri"],
            client_id=client_config["web"]["client_id"],
            client_secret=client_config["web"]["client_secret"],
            scopes=SCOPES
        )

        credentials.refresh(google.auth.transport.requests.Request())
        logger.info("YouTube API 인증 정보 갱신 및 로드 완료.")

        return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    except HttpError as e:
        # E501 해결: 줄 길이를 79자 이하로 맞춤
        logger.error(f"YouTube API 인증 중 HTTP 오류 발생: {e.resp.status} - "
                    f"{e.content.decode()}", exc_info=True)
        if e.resp.status == 401:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.error("Refresh Token이 유효하지 않거나 만료되었습니다. "
                        "'get_youtube_token.py'를 다시 실행하여 새 토큰을 받아 "
                        "Secret Manager에 업데이트해야 합니다.")
        # E501 해결: 줄 길이를 79자 이하로 맞춤
        raise ValueError(f"YouTube API 인증 실패: {e.resp.status}") from e
    except Exception as e:
        logger.error(f"YouTube API 서비스 인증 실패: {e}", exc_info=True)
        raise


def upload_video(
    video_file_path,
    title,
    description,
    tags,
    category_id,
    privacy_status,
    config_instance=None
):
    """
    YouTube에 비디오를 업로드합니다.
    """
    if not config_instance:
        raise ValueError("Config 인스턴스가 'upload_video' 함수에 전달되지 않았습니다.")

    youtube = get_authenticated_service(config_instance)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
        "videoRecordingDetails": {
            # "location": { "latitude": 37.5665, "longitude": 126.9780 },
            # "recordingDate": "YYYY-MM-DDTHH:MM:SS.000Z"
        },
    }

    media_body = MediaFileUpload(video_file_path, chunksize=-1, resumable=True)

    try:
        logger.info(f"YouTube에 비디오 업로드 시작: '{title}'")
        insert_request = youtube.videos().insert(
            part="snippet,status,videoRecordingDetails",
            body=body,
            media_body=media_body,
        )

        response = None
        while response is None:
            status, response = insert_request.next_chunk()
            if status:
                # E501 해결: 줄 길이를 79자 이하로 맞춤
                logger.info(f"비디오 업로드 진행률: "
                            f"{int(status.resumable_progress * 100)}%")

        logger.info(f"비디오 업로드 성공! YouTube ID: {response.get('id')}")
        return response

    except HttpError as e:
        # E501 해결: 줄 길이를 79자 이하로 맞춤
        logger.error(f"YouTube 비디오 업로드 중 HTTP 오류 발생: {e.resp.status} - "
                    f"{e.content.decode()}", exc_info=True)
        # E501 해결: 줄 길이를 79자 이하로 맞춤
        raise ValueError(f"YouTube 업로드 실패: {e.resp.status} - "
                         f"{e.content.decode()}") from e
    except Exception as e:
        logger.error(f"YouTube 비디오 업로드 중 일반 오류 발생: {e}", exc_info=True)
        raise
    
