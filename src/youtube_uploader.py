# src/youtube_uploader.py
import logging
import os
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from src.config import load_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for YouTube API
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

def get_authenticated_service(config):
    """
    Authenticates with YouTube API using OAuth 2.0 credentials from GCP Secret Manager/GitHub Secrets.
    """
    credentials_data = config.get("YOUTUBE_OAUTH_CREDENTIALS")
    if not credentials_data:
        logging.error("YouTube OAuth credentials not found.")
        return None

    # The credentials_data should be a dictionary containing client_id, client_secret, refresh_token.
    # The InstalledAppFlow expects a specific structure for the client_config.
    # We are simulating a pre-authorized flow using the refresh token.
    
    # Constructing a Credentials object from the stored data
    try:
        credentials = Credentials.from_authorized_user_info(
            info=credentials_data, # This should contain 'client_id', 'client_secret', 'refresh_token'
            scopes=SCOPES
        )
        
        if not credentials.valid:
            if credentials.expired and credentials.refresh_token:
                logging.info("Refreshing expired YouTube OAuth token...")
                credentials.refresh(Request())
            else:
                logging.error("Invalid or expired YouTube OAuth credentials and no refresh token available.")
                return None
        
        logging.info("YouTube API authentication successful.")
        return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    except Exception as e:
        logging.error(f"Error during YouTube API authentication: {e}")
        logging.error("Please ensure YOUTUBE_OAUTH_CREDENTIALS in Secret Manager is a valid JSON with client_id, client_secret, and a fresh refresh_token.")
        logging.error("You might need to run an OAuth flow locally once to get a refresh token.")
        return None

def upload_video(video_path, content, config):
    """
    Uploads a video to YouTube.
    content dict should contain 'title', 'description', 'thumbnail_path'.
    """
    youtube = get_authenticated_service(config)
    if not youtube:
        logging.error("YouTube service not authenticated. Cannot upload video.")
        return False

    if not os.path.exists(video_path):
        logging.error(f"Video file not found: {video_path}. Cannot upload.")
        return False

    body = {
        "snippet": {
            "title": content.get("title", "Generated Video Title"),
            "description": content.get("description", "Generated video description."),
            "tags": ["shorts", "AI generated", "automation", "trending", "youtube shorts"], # Example tags
            "categoryId": "22",  # Category ID for "People & Blogs". Adjust as needed.
            "defaultLanguage": "ko"
        },
        "status": {
            "privacyStatus": "private",  # Start as private for processing
            "selfDeclaredMadeForKids": False # Adjust based on content
        },
        "recordingDetails": {
            "recordingDate": datetime.now().isoformat() + "Z"
        }
    }

    media_body = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)

    try:
        logging.info(f"Uploading video: {content.get('title')}...")
        insert_request = youtube.videos().insert(
            part="snippet,status,recordingDetails",
            body=body,
            media_body=media_body
        )
        response = insert_request.execute()
        video_id = response.get("id")
        logging.info(f"Video uploaded successfully. Video ID: {video_id}")

        # Set thumbnail if available
        thumbnail_path = content.get("thumbnail_path")
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                logging.info(f"Setting thumbnail for video {video_id} from {thumbnail_path}...")
                thumbnail_media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg", resumable=True)
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=thumbnail_media
                ).execute()
                logging.info(f"Thumbnail set successfully for video {video_id}.")
            except HttpError as e:
                logging.warning(f"Could not set thumbnail for video {video_id}: {e}")
            except Exception as e:
                logging.warning(f"An error occurred while setting thumbnail: {e}")
        else:
            logging.warning("No thumbnail path provided or thumbnail file not found. Skipping thumbnail set.")

        # Update privacy status to public after successful upload and thumbnail set
        logging.info(f"Updating video {video_id} privacy status to public...")
        youtube.videos().update(
            part="status",
            body={
                "id": video_id,
                "status": {"privacyStatus": "public"}
            }
        ).execute()
        logging.info(f"Video {video_id} is now public.")

        # Add a comment (optional)
        # post_comment(youtube, video_id, "Generated automatically by AI! Please subscribe for more content!")

        return True

    except HttpError as e:
        logging.error(f"An HTTP error occurred during video upload: {e.resp.status} - {e.content}")
        logging.error("Check YouTube API quotas, authentication, and video content for policy violations.")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during video upload: {e}")
        return False

def post_comment(youtube_service, video_id, comment_text):
    """Posts a comment to the uploaded video."""
    try:
        logging.info(f"Posting comment to video {video_id}...")
        comment_thread = youtube_service.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": comment_text
                        }
                    }
                }
            }
        ).execute()
        logging.info(f"Comment posted successfully: {comment_thread['snippet']['topLevelComment']['snippet']['textOriginal']}")
        return True
    except HttpError as e:
        logging.warning(f"Could not post comment to video {video_id}: {e.resp.status} - {e.content}")
        return False
    except Exception as e:
        logging.warning(f"An unexpected error occurred while posting comment: {e}")
        return False
