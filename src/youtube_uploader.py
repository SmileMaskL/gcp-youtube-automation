import os
import google_auth_oauthlib.flow
import google.auth.transport.requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import json
from src.config import YOUTUBE_OAUTH_CREDENTIALS, GCP_PROJECT_ID
from src.monitoring import log_system_health
from google.cloud import secretmanager
from google.oauth2 import service_account

# Secret Manager 클라이언트 초기화
def get_secret_client_for_youtube():
    try:
        service_account_info = json.loads(os.getenv("GCP_SERVICE_ACCOUNT_KEY"))
        credentials = service_account.Credentials.from_service_account_info(service_account_info)
        return secretmanager.SecretManagerServiceClient(credentials=credentials)
    except Exception as e:
        log_system_health(f"Error initializing Secret Manager client for YouTube: {e}", level="error")
        return None

SECRET_CLIENT_YOUTUBE = get_secret_client_for_youtube()

def update_youtube_oauth_secret(new_credentials_json_string):
    """
    업데이트된 YouTube OAuth 자격 증명 (리프레시 토큰 포함)을 GitHub Secret에 다시 저장합니다.
    (이 함수는 GitHub Actions 환경에서 Secret을 업데이트하는 직접적인 방법이 없으므로,
    실제 GitHub Actions 워크플로우에서는 Secret Manager를 통해 관리하는 것이 더 적합합니다.
    여기서는 Secret Manager에 저장된 Secret을 업데이트하는 로직을 가정합니다.)
    """
    secret_id = "youtube-oauth-credentials" # Secret Manager의 Secret ID

    if SECRET_CLIENT_YOUTUBE and GCP_PROJECT_ID:
        parent = f"projects/{GCP_PROJECT_ID}/secrets/{secret_id}"
        try:
            # 기존 Secret에 새 버전 추가
            response = SECRET_CLIENT_YOUTUBE.add_secret_version(
                request={"parent": parent, "payload": {"data": new_credentials_json_string.encode("UTF-8")}}
            )
            log_system_health(f"YouTube OAuth credentials in Secret Manager updated: {response.name}", level="info")
            return True
        except Exception as e:
            log_system_health(f"Failed to update YouTube OAuth credentials in Secret Manager: {e}", level="error")
            return False
    else:
        log_system_health("Secret Manager 클라이언트 또는 GCP Project ID가 설정되지 않아 YouTube OAuth Secret을 업데이트할 수 없습니다.", level="warning")
        return False


def get_authenticated_service():
    """
    YouTube Data API 서비스에 대한 인증된 객체를 반환합니다.
    GitHub Secret에서 OAuth 자격 증명을 로드하고, 필요시 새로 인증하거나 토큰을 갱신합니다.
    """
    if not YOUTUBE_OAUTH_CREDENTIALS:
        log_system_health("YOUTUBE_OAUTH_CREDENTIALS GitHub Secret이 설정되지 않았습니다.", level="critical")
        raise ValueError("YouTube OAuth credentials are not set.")

    # 환경 변수에서 JSON 문자열로 자격 증명 로드
    credentials_data = json.loads(YOUTUBE_OAUTH_CREDENTIALS)

    # credential 객체 생성
    try:
        # 이전에 저장된 refresh_token이 있다면 자동으로 사용
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            client_config={
                "installed": {
                    "client_id": credentials_data.get("client_id", credentials_data.get("web", {}).get("client_id")),
                    "client_secret": credentials_data.get("client_secret", credentials_data.get("web", {}).get("client_secret")),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
                }
            },
            scopes=["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
        )

        # 리프레시 토큰이 포함된 자격 증명을 직접 로드
        if "token" in credentials_data and "refresh_token" in credentials_data:
            credentials = google.oauth2.credentials.Credentials.from_authorized_user_info(credentials_data, flow.scopes)
            log_system_health("Loaded existing YouTube OAuth credentials.", level="info")
        else:
            log_system_health("No refresh token found. Initiating new authorization flow (might require manual step if not handled via refresh token).", level="warning")
            # 이 부분은 GitHub Actions에서는 동작하지 않음.
            # 로컬에서 initial authentication을 통해 refresh_token을 얻어와야 함.
            # GitHub Actions에서는 이미 refresh_token이 포함된 credentials JSON을 기대함.
            # (따라서 YOUTUBE_OAUTH_CREDENTIALS Secret에 refresh_token이 들어있는 JSON을 저장해야 함)
            raise ValueError("YOUTUBE_OAUTH_CREDENTIALS must contain a valid refresh token for non-interactive environments.")

        # 토큰 만료 시 자동 갱신
        if credentials.expired and credentials.refresh_token:
            log_system_health("YouTube OAuth token expired, attempting to refresh...", level="info")
            credentials.refresh(google.auth.transport.requests.Request())
            log_system_health("YouTube OAuth token refreshed successfully.", level="info")
            # 갱신된 자격 증명을 Secret에 다시 저장 (중요)
            updated_credentials_json = credentials.to_json()
            update_youtube_oauth_secret(updated_credentials_json)
        elif credentials.expired and not credentials.refresh_token:
            log_system_health("YouTube OAuth token expired and no refresh token available. Manual re-authentication required.", level="critical")
            raise ValueError("YouTube OAuth token expired and no refresh token available. Manual re-authentication required.")

        return build("youtube", "v3", credentials=credentials)
    except Exception as e:
        log_system_health(f"YouTube 인증 오류: {e}", level="critical")
        raise ValueError(f"YouTube 인증에 실패했습니다: {e}")

def upload_video(video_path, thumbnail_path, title, description, tags, category_id="22", privacy_status="public"):
    """
    YouTube에 비디오를 업로드합니다.
    category_id 22는 'People & Blogs'입니다. Shorts는 'Entertainment' (24) 또는 'Comedy' (23) 등도 고려.
    """
    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
            "defaultLanguage": "ko",
            "localized": {
                "title": title,
                "description": description
            }
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False # 아동용 아님
        },
        "recordingDetails": {
            "recordingDate": datetime.datetime.now().isoformat() + "Z"
        }
    }

    # 썸네일 업로드
    media_body = MediaFileUpload(video_path, resumable=True)

    try:
        insert_request = youtube.videos().insert(
            part="snippet,status,recordingDetails",
            body=body,
            media_body=media_body
        )

        response = None
        while response is None:
            status, response = insert_request.next_chunk()
            if status:
                log_system_health(f"YouTube 비디오 업로드 진행률: {int(status.progress() * 100)}%", level="info")

        video_id = response.get("id")
        log_system_health(f"비디오가 성공적으로 업로드되었습니다. 비디오 ID: {video_id}", level="info")

        # 썸네일 설정
        if thumbnail_path and os.path.exists(thumbnail_path):
            thumbnail_media = MediaFileUpload(thumbnail_path)
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=thumbnail_media
                ).execute()
                log_system_health(f"썸네일이 비디오 ID {video_id}에 성공적으로 설정되었습니다.", level="info")
            except HttpError as e:
                log_system_health(f"썸네일 설정 중 오류 발생: {e}", level="error")
        else:
            log_system_health("썸네일 파일이 존재하지 않거나 경로가 잘못되었습니다. 썸네일 설정을 건너뜝니다.", level="warning")

        # 댓글 자동 포스팅 (임시로 여기에 포함)
        # from src.comment_poster import post_comment
        # generated_comments = generate_youtube_comments(title) # content_generator에서 가져옴
        # for comment_text in generated_comments:
        #     try:
        #         post_comment(video_id, comment_text)
        #     except Exception as e:
        #         log_system_health(f"댓글 '{comment_text}' 포스팅 중 오류 발생: {e}", level="error")


        return video_id

    except HttpError as e:
        log_system_health(f"YouTube API 오류 발생: {e.resp.status}, {e.content.decode()}", level="error")
        raise ValueError(f"YouTube 업로드 실패: {e.content.decode()}")
    except Exception as e:
        log_system_health(f"비디오 업로드 중 예상치 못한 오류 발생: {e}", level="error")
        raise ValueError(f"비디오 업로드 실패: {e}")

# import datetime # 상단에 추가해야 함
