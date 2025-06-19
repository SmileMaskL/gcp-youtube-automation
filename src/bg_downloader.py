# src/bg_downloader.py
import requests
import logging
import os

logger = logging.getLogger(__name__)

def download_pexels_videos(api_key: str, query: str, orientation: str = 'landscape', size: str = 'medium', max_videos: int = 1):
    """
    Pexels API에서 배경 동영상 URL을 검색합니다.

    Args:
        api_key (str): Pexels API 키.
        query (str): 검색할 키워드.
        orientation (str): 'landscape' (가로), 'portrait' (세로), 'square' (정사각형). Shorts에 유리하게 'portrait'도 고려.
        size (str): 'small', 'medium', 'large'.
        max_videos (int): 검색할 최대 동영상 수.

    Returns:
        str: 가장 적합한 동영상 URL, 또는 None.
    """
    if not api_key:
        logger.error("Pexels API Key is not provided.")
        return None

    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "orientation": orientation,
        "size": size,
        "per_page": max_videos,
        "page": 1
    }

    # Shorts는 세로 영상이므로 'portrait'를 우선적으로 시도
    if orientation == 'landscape' and query.lower() not in ['nature', 'abstract']: # 특정 키워드 외에는 세로 영상 시도
         params['orientation'] = 'portrait'

    try:
        response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        videos = data.get("videos", [])
        if not videos:
            logger.warning(f"No videos found for query '{query}' with orientation '{orientation}'. Trying landscape...")
            # 세로 영상이 없으면 가로 영상으로 재시도
            if params['orientation'] == 'portrait':
                params['orientation'] = 'landscape'
                response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                videos = data.get("videos", [])
                if not videos:
                    logger.error(f"No videos found for query '{query}' even with landscape orientation.")
                    return None

        # 가장 해상도가 높은 동영상 URL 선택
        best_video_url = None
        max_quality = 0

        for video in videos:
            for video_file in video.get("video_files", []):
                quality = video_file.get("quality") # 'hd', 'sd' 등
                link = video_file.get("link")
                if quality == 'hd' and link and (best_video_url is None or video_file.get("width") * video_file.get("height") > max_quality):
                    best_video_url = link
                    max_quality = video_file.get("width") * video_file.get("height")

        if best_video_url:
            logger.info(f"Found best video URL for '{query}': {best_video_url}")
            return best_video_url
        else:
            logger.warning(f"No suitable video link found for query '{query}'.")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching videos from Pexels API: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred in bg_downloader: {e}", exc_info=True)
        return None

if __name__ == '__main__':
    from dotenv import load_dotenv
    from src.config import setup_logging
    load_dotenv()
    setup_logging()

    pexels_api_key = os.environ.get("PEXELS_API_KEY")
    if not pexels_api_key:
        print("Please set PEXELS_API_KEY environment variable for local testing.")
    else:
        print("--- Searching Pexels videos (portrait) ---")
        video_link = download_pexels_videos(pexels_api_key, "city night", orientation='portrait')
        if video_link:
            print(f"Found video link: {video_link}")
        else:
            print("No portrait video found. Trying landscape...")
            video_link = download_pexels_videos(pexels_api_key, "city night", orientation='landscape')
            if video_link:
                print(f"Found video link: {video_link}")
            else:
                print("No video found for 'city night'.")

        print("\n--- Searching Pexels videos (nature) ---")
        video_link = download_pexels_videos(pexels_api_key, "nature abstract")
        if video_link:
            print(f"Found video link: {video_link}")
        else:
            print("No video found for 'nature abstract'.")
