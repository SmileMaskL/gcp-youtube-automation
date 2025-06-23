# src/youtube_utils.py
import logging
from googleapiclient.discovery import build # F401 'googleapiclient.discovery.build' 사용되므로 유지
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class YouTubeUtils:
    def __init__(self, youtube_service):
        self.youtube = youtube_service
        logger.info("YouTubeUtils initialized.")

    def get_channel_info(self, channel_id=None, for_username=None):
        """
        Retrieves information about a YouTube channel.
        """
        try:
            if channel_id:
                request = self.youtube.channels().list(
                    part="snippet,contentDetails,statistics",
                    id=channel_id
                )
            elif for_username:
                request = self.youtube.channels().list(
                    part="snippet,contentDetails,statistics",
                    forUsername=for_username
                )
            else:
                raise ValueError("Must provide either channel_id or for_username.")

            response = request.execute()
            if response and response.get('items'):
                # E501 해결: 줄 길이를 79자 이하로 맞춤
                logger.info(f"Channel info retrieved for {channel_id or for_username}.")
                return response['items'][0]
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.warning(f"No channel info found for {channel_id or for_username}.")
            return None
        except HttpError as e:
            logger.error(f"Error getting channel info: {e}", exc_info=True)
            return None
        except Exception as e:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.error(f"An unexpected error occurred getting channel info: {e}",
                        exc_info=True)
            return None

    def search_videos(self, query, max_results=10, order="relevance"):
        """
        Searches for videos on YouTube.
        """
        try:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.info(f"Searching videos for query '{query}', max results: "
                        f"{max_results}")
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=max_results,
                order=order
            )
            response = request.execute()
            items = response.get('items', [])
            logger.info(f"Found {len(items)} videos for query '{query}'.")
            return items
        except HttpError as e:
            logger.error(f"Error searching videos: {e}", exc_info=True)
            return []
        except Exception as e:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.error(f"An unexpected error occurred searching videos: {e}",
                        exc_info=True)
            return []

    def get_video_details(self, video_ids):
        """
        Retrieves details for a list of video IDs.
        """
        if not video_ids:
            return []
        try:
            video_ids_str = ','.join(video_ids[:50])
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.info(f"Getting details for video IDs: {video_ids_str[:100]}...")
            request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_ids_str
            )
            response = request.execute()
            items = response.get('items', [])
            logger.info(f"Retrieved details for {len(items)} videos.")
            return items
        except HttpError as e:
            logger.error(f"Error getting video details: {e}", exc_info=True)
            return []
        except Exception as e:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.error(f"An unexpected error occurred getting video details: {e}",
                        exc_info=True)
            return []

    def get_video_comments(self, video_id, max_results=20):
        """
        Retrieves top-level comments for a given video.
        """
        try:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.info(f"Getting comments for video ID: {video_id}, "
                        f"max results: {max_results}")
            request = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                textFormat="plainText",
                maxResults=max_results
            )
            response = request.execute()
            comments = [item['snippet']['topLevelComment']['snippet']
                        for item in response.get('items', [])]
            logger.info(f"Found {len(comments)} comments for video {video_id}.")
            return comments
        except HttpError as e:
            logger.error(f"Error getting video comments: {e}", exc_info=True)
            return []
        except Exception as e:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.error(f"An unexpected error occurred getting video comments: {e}",
                        exc_info=True)
            return []

    def get_most_viewed_shorts(self, region_code='US', max_results=10):
        """
        Fetches most viewed Shorts in a specific region.
        """
        try:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.info(f"Searching for most viewed shorts in region {region_code}")
            request = self.youtube.videos().list(
                part="snippet,statistics",
                chart="mostPopular",
                regionCode=region_code,
                videoCategoryId="22",
                maxResults=max_results
            )
            response = request.execute()
            items = response.get('items', [])
            logger.info(f"Found {len(items)} popular videos in {region_code}.")
            return items
        except HttpError as e:
            logger.error(f"Error getting most viewed shorts: {e}", exc_info=True)
            return []
        except Exception as e:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.error(f"An unexpected error occurred getting most viewed shorts: {e}",
                        exc_info=True)
            return []
    
