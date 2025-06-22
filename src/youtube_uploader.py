# youtube_uploader.py
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import logging
from google.oauth2.credentials import Credentials
import json # JSON 임포트

logging.basicConfig(level=logging.INFO)

def upload_video(file_path, title, description, tags, category_id, privacy_status):
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"

    # 환경 변수에서 인증 정보 로드
    CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
    REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        logging.error("Missing YouTube API credentials in environment variables.")
        raise ValueError("YouTube API credentials (CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN) must be set.")

    # Refresh Token을 사용하여 자격 증명 객체 생성 및 갱신
    # 이 부분이 중요합니다! 한 번 발급받은 Refresh Token으로 Access Token을 갱신합니다.
    credentials = Credentials(
        token=None,  # Access Token은 갱신될 것이므로 초기에는 None
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]
    )

    try:
        # Access Token 갱신 시도
        credentials.refresh(google.auth.transport.requests.Request())
        logging.info("YouTube API access token refreshed successfully.")
    except Exception as e:
        logging.error(f"Failed to refresh YouTube API access token: {e}")
        raise # 토큰 갱신 실패 시 오류 발생

    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }

    try:
        logging.info(f"Attempting to upload video: {title} from {file_path}")
        # MediaFileUpload는 파일 경로를 받습니다.
        media_body = googleapiclient.http.MediaFileUpload(file_path, mimetype="video/mp4", resumable=True)

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media_body
        )
        response = request.execute()
        logging.info(f"Video uploaded successfully. Video ID: {response.get('id')}")
        logging.info(f"Video URL: https://www.youtube.com/watch?v={response.get('id')}")
        return response
    except googleapiclient.errors.HttpError as e:
        error_content = e.content.decode('utf-8')
        logging.error(f"YouTube API HttpError occurred: {e.resp.status}")
        logging.error(f"YouTube API Error Details: {error_content}")
        raise # 오류를 다시 발생시켜 상위 호출자가 처리할 수 있도록 함
    except Exception as e:
        logging.error(f"An unexpected error occurred during video upload: {e}")
        raise

# 이 파일은 주로 다른 파일에서 임포트하여 사용됩니다.
# main.py에서 이 함수를 호출할 것입니다.
