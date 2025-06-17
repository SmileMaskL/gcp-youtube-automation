"""
배경 영상 다운로더 (최종 수정본)
"""
import requests
import logging
from pathlib import Path
from .config import Config
import uuid

logger = logging.getLogger(__name__)

def download_background_video(query: str) -> str:
    """Pexels에서 배경 영상 다운로드"""
    try:
        video_path = Config.TEMP_DIR / f"bg_{uuid.uuid4()}.mp4"
        
        # API 요청
        headers = {"Authorization": Config.get_api_key("PEXELS_API_KEY")}
        params = {"query": query, "per_page": 5, "size": "small"}
        
        response = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        
        # 영상 선택 및 다운로드
        videos = response.json().get("videos", [])
        if not videos:
            raise ValueError("검색 결과 없음")
            
        video = videos[0]  # 가장 관련성 높은 영상 선택
        video_file = next(
            (f for f in video["video_files"] 
            if f.get("width") == Config.SHORTS_WIDTH),
            video["video_files"][0]
        )
        
        with requests.get(video_file["link"], stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        logger.info(f"배경 영상 다운로드 완료: {video_path}")
        return str(video_path)
        
    except Exception as e:
        logger.error(f"배경 영상 다운로드 실패: {e}")
        raise
