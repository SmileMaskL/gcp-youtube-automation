# src/youtube_uploader.py (예시, 실제 파일에 맞게 수정)

import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import logging
from google.cloud import secretmanager # Secret Manager를 직접 사용할 경우

logger = logging.getLogger(__name__)

# 기존의 Secret Manager에서 OAuth 자격 증명을 가져오는 로직은 유지하거나,
# 새로 전달받는 client_id, client_secret, refresh_token을 사용하도록 변경해야 합니다.
# 여기서는 편의를 위해 직접 전달받는 방식으로 수정합니다.

class YouTubeUploader:
    def __init__(self, project_id, bucket_name, client_id, client_secret, refresh_token):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.credentials = self._get_credentials()
        self.youtube = self._get_youtube_service()

    def _get_credentials(self):
        # 전달받은 client_id, client_secret, refresh_token으로 Credential 객체 생성
        credentials = google.oauth2.credentials.Credentials(
            token=None,  # 초기 액세스 토큰은 None
            refresh_token=self.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
        )
        # credentials.refresh(google.auth.transport.requests.Request()) # 필요시 토큰 갱신
        return credentials

    def _get_youtube_service(self):
        return googleapiclient.discovery.build(
            "youtube", "v3", credentials=self.credentials
        )

    # ... (나머지 업로드 로직은 동일) ...
    async def upload_video(self, video_path, title, description, tags, thumbnail_path=None):
        # ... (기존 로직) ...
        # self.youtube 객체를 사용하여 업로드 로직을 구현합니다.
        # 예시:
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "22" # 예시 카테고리
            },
            "status": {
                "privacyStatus": "public" # 예시 프라이버시 상태
            }
        }
        
        # media = googleapiclient.http.MediaFileUpload(video_path, resumable=True)
        # request = self.youtube.videos().insert(
        #     part="snippet,status",
        #     body=body,
        #     media_body=media
        # )
        # response = request.execute()
        # logger.info(f"Video uploaded with ID: {response['id']}")
        # return response['id']
        # ... (이하 실제 업로드 로직) ...
        logger.info(f"Uploading video: {video_path} with title: {title}")
        # 실제 업로드 로직을 여기에 구현해야 합니다.
        # 이 부분은 당신의 기존 YouTubeUploader 클래스 구현에 따라 달라집니다.
        # credentials.refresh()가 제대로 작동하는지 확인하세요.
        try:
            from googleapiclient.http import MediaFileUpload
            
            # OAuth2 Refresh Token을 사용하여 Access Token을 갱신합니다.
            # 이 과정이 Cloud Function 환경에서 제대로 이루어져야 합니다.
            request = google.auth.transport.requests.Request()
            self.credentials.refresh(request)
            
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': '22' # config.youtube_category_id 사용 고려
                },
                'status': {
                    'privacyStatus': 'public' # config.youtube_privacy_status 사용 고려
                }
            }

            media_body = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)

            insert_request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media_body
            )

            # 비디오 업로드 실행
            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    logger.info("Uploaded %d%%." % int(status.progress() * 100))
            
            video_id = response.get('id')
            logger.info(f"Video uploaded. Video ID: {video_id}")

            # 썸네일 업로드
            if thumbnail_path and os.path.exists(thumbnail_path):
                thumbnail_media_body = MediaFileUpload(thumbnail_path, mimetype='image/jpeg', resumable=True)
                set_thumbnail_request = self.youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=thumbnail_media_body
                )
                set_thumbnail_response = set_thumbnail_request.execute()
                logger.info(f"Thumbnail uploaded for video ID: {video_id}")
            
            return video_id

        except googleapiclient.errors.ResumableUploadError as e:
            logger.error(f"ResumableUploadError during video upload: {e}")
            raise
        except googleapiclient.errors.HttpError as e:
            logger.error(f"HTTP Error during video upload: {e}")
            if e.resp.status == 401:
                logger.error("401 Unauthorized: YouTube API token expired or invalid. Please check refresh token and re-authenticate.")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during video upload: {e}", exc_info=True)
            raise
