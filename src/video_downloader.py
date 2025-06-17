import os
import logging
import requests
from typing import Optional
from pathlib import Path
from .config import Config

logger = logging.getLogger(__name__)

def download_video(query: str) -> str:
    """
    Pexels에서 배경 영상 다운로드
    (무료 스톡 영상 사용으로 저작권 문제 없음)
    """
    try:
        # 임시 디렉토리 생성
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Pexels API로 영상 검색 (무료 API)
        headers = {"Authorization": Config.get_api_key("PEXELS_API_KEY")}
        search_url = f"https://api.pexels.com/videos/search?query={query}&per_page=1"
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        
        video_data = response.json()
        if not video_data.get('videos'):
            raise ValueError("적합한 영상을 찾을 수 없습니다")
            
        # 가장 인기 있는 무료 영상 선택
        video_file = video_data['videos'][0]['video_files'][0]['link']
        
        # 영상 다운로드
        video_path = os.path.join(temp_dir, f"bg_{os.urandom(8).hex()}.mp4")
        with requests.get(video_file, stream=True) as r:
            r.raise_for_status()
            with open(video_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        logger.info(f"배경 영상 다운로드 완료: {video_path}")
        return video_path
        
    except Exception as e:
        logger.error(f"영상 다운로드 실패: {e}")
        # 실패 시 기본 배경 영상 사용
        default_path = os.path.join(temp_dir, "default_bg.mp4")
        if not os.path.exists(default_path):
            # 기본 영상 다운로드 (저작권 없는 영상)
            default_url = "https://example.com/free-stock-video.mp4"  # 실제 무료 영상 URL로 교체 필요
            with requests.get(default_url, stream=True) as r:
                with open(default_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        return default_path
