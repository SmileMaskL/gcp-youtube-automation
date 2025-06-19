import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self):
        self.api_key = os.getenv("PEXELS_API_KEY")
        self.base_url = "https://api.pexels.com/videos/search"
        
    def download_video(self, query: str) -> Optional[str]:
        try:
            headers = {"Authorization": self.api_key}
            params = {
                "query": query + " background",
                "per_page": 3,
                "orientation": "portrait",
                "size": "small"
            }
            
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            videos = response.json().get('videos', [])
            if not videos:
                logger.warning(f"검색 결과 없음: {query}")
                return None
                
            # 가장 작은 크기의 동영상 선택
            video_file = min(videos[0]['video_files'], key=lambda x: x['width'])['link']
            os.makedirs("temp", exist_ok=True)
            video_path = f"temp/bg_{query.replace(' ', '_')}.mp4"
            
            with requests.get(video_file, stream=True, timeout=20) as r:
                r.raise_for_status()
                with open(video_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            return video_path
            
        except Exception as e:
            logger.error(f"비디오 다운로드 실패: {str(e)}")
            return None

def download_background(query: str) -> str:
    downloader = VideoDownloader()
    for attempt in range(3):
        video_path = downloader.download_video(query)
        if video_path:
            return video_path
        logger.warning(f"재시도 {attempt + 1}/3")
    
    raise ValueError(f"'{query}'에 대한 배경 영상을 찾을 수 없습니다")
