import random
import requests
import uuid
from pathlib import Path
from .config import Config
import logging

logger = logging.getLogger(__name__)

def download_background_video(query):
    """Pexels에서 배경 영상 다운로드"""
    video_path = Config.TEMP_DIR / f"bg_{uuid.uuid4()}.mp4"
    try:
        headers = {"Authorization": Config.get_api_key("PEXELS_API_KEY")}
        params = {"query": query, "per_page": 5, "size": "small"}
        
        # 1. 영상 검색
        search_url = "https://api.pexels.com/videos/search"
        response = requests.get(search_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        videos = response.json().get("videos", [])
        if not videos:
            raise ValueError("검색 결과 없음")
            
        # 2. 랜덤 영상 선택
        video = random.choice(videos)
        video_file = next(
            (f for f in video["video_files"] if f.get("width") == Config.SHORTS_WIDTH),
            video["video_files"][0]  # fallback
        )
        
        # 3. 영상 다운로드
        with requests.get(video_file["link"], stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        logger.info(f"배경 영상 다운로드 완료: {video_path}")
        return video_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Pexels API 오류: {e}")
        raise
    except Exception as e:
        logger.error(f"배경 영상 다운로드 실패: {e}")
        raise
