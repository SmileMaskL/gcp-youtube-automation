import logging
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class YouTubeUploader:
    """
    A class to handle YouTube video uploads and credential management.
    """

    def __init__(self, credentials_json: dict):
        """
        Initializes the YouTubeUploader with credentials.

        Args:
            credentials_json (dict): A dictionary containing 'client_id',
                                     'client_secret', and 'refresh_token'.
        """
        self.credentials_json = credentials_json
        self.creds = None
        self.youtube = None
        self._authenticate()

    def _authenticate(self):
        """
        Authenticates with YouTube API using the provided credentials.
        Refreshes the token if necessary.
        """
        client_id = self.credentials_json.get("client_id")
        client_secret = self.credentials_json.get("client_secret")
        refresh_token = self.credentials_json.get("refresh_token")

        if not all([client_id, client_secret, refresh_token]):
            logging.error("Missing client_id, client_secret, or refresh_token in credentials_json.")
            raise ValueError("Incomplete credentials for YouTube API.")

        try:
            self.creds = Credentials(
                token=None,  # Token will be refreshed
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret
            )
            # Attempt to refresh the token immediately to ensure it's valid
            self.creds.refresh(Request())
            self.youtube = build("youtube", "v3", credentials=self.creds)
            logging.info("✅ YouTube API authenticated successfully.")
        except RefreshError as e:
            logging.error(f"Failed to refresh access token: {e}")
            raise ConnectionRefusedError("Could not authenticate with YouTube. Check your refresh token.")
        except Exception as e:
            logging.error(f"An unexpected error occurred during authentication: {e}")
            raise

    async def revoke_credentials(self):
        """
        Revokes the current YouTube API credentials.
        This will invalidate the refresh token.
        """
        if self.creds and self.creds.valid and self.creds.token:
            try:
                self.creds.revoke(Request())
                logging.info("✅ YouTube API credentials revoked successfully.")
                self.creds = None
                self.youtube = None
            except Exception as e:
                logging.error(f"Failed to revoke credentials: {e}")
                raise
        else:
            logging.warning("No active credentials to revoke or credentials are invalid/expired.")

    def upload(self, video_path: str, title: str, description: str, keywords: list = None):
        """
        Uploads a video to YouTube.

        Args:
            video_path (str): The file path to the video to upload.
            title (str): The title of the video.
            description (str): The description of the video.
            keywords (list, optional): A list of tags/keywords for the video.
                                       Defaults to ["AI Shorts", "Automation"].

        Returns:
            str: The ID of the uploaded video.
        """
        if not self.youtube:
            logging.error("YouTube service not initialized. Attempting to re-authenticate.")
            self._authenticate() # Try to re-authenticate if service is missing

        if not self.youtube: # Check again after re-authentication attempt
            raise ConnectionError("YouTube service is not available. Cannot upload video.")

        if keywords is None:
            keywords = ["AI Shorts", "Automation"]

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": keywords,
                "categoryId": "28"  # Category ID for Science & Technology
            },
            "status": {
                "privacyStatus": "public",  # Can be 'public', 'private', or 'unlisted'
                "selfDeclaredMadeForKids": False
            }
        }

        try:
            logging.info(f"Attempting to upload video from: {video_path}")
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=video_path  # This should be a path to the video file
            )
            response = request.execute()
            video_id = response.get('id')
            if video_id:
                logging.info(f"✅ Uploaded video ID: {video_id}")
                return video_id
            else:
                logging.error(f"Video upload successful but no ID returned: {response}")
                raise RuntimeError("Video upload failed to return a video ID.")
        except Exception as e:
            logging.error(f"Error during video upload: {e}")
            raise

# Example usage (for demonstration purposes, typically you'd load credentials from a file)
if __name__ == "__main__":
    # IMPORTANT: Replace with your actual client_id, client_secret, and refresh_token
    # In a real application, these would be loaded securely, e.g., from environment variables
    # or a secure configuration file, NOT hardcoded.
    mock_credentials = {
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET",
        "refresh_token": "YOUR_REFRESH_TOKEN"
    }

    # Create a dummy video file for testing purposes
    # In a real scenario, video_path would point to an actual video file
    dummy_video_path = "path/to/your/video.mp4"
    try:
        # For actual testing, ensure a valid video file exists at dummy_video_path
        # and replace mock_credentials with your actual credentials.
        # This part will likely fail if a real video file and valid credentials aren't provided.
        uploader = YouTubeUploader(mock_credentials)
        
        # Example upload call (this will fail without a real video file and valid credentials)
        # video_id = uploader.upload(
        #     video_path=dummy_video_path,
        #     title="My Awesome AI Short",
        #     description="This is an automated AI-generated short video!",
        #     keywords=["AI", "Shorts", "Test", "Python"]
        # )
        # print(f"Successfully uploaded video with ID: {video_id}")

        # Example of revoking credentials
        # await uploader.revoke_credentials() # Note: revoke_credentials is async, requires await in an async context
        print("Uploader initialized. To test upload/revoke, replace mock credentials and video path.")

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except ConnectionRefusedError as e:
        print(f"Authentication Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

