# src/youtube_uploader.py

import os
import logging
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def upload_video_to_youtube(client_id, client_secret, refresh_token, video_path, title, description):
    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    creds.refresh(Request())

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["AI Shorts", "Automation"],
            "categoryId": "28"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        }
    }

    try:
        insert_request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=video_path
        )
        response = insert_request.execute()
        logger.info(f"✅ Video uploaded. Video ID: {response['id']}")
    except Exception as e:
        logger.error(f"❌ Video upload failed: {e}")
        raise
