import os
import random
import uuid
import requests
from pathlib import Path
from config import Config
from pexels_api import API
from retrying import retry
import subprocess
import logging

logger = logging.getLogger(__name__)

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def get_background_video(query):
    """배경 영상 가져오기"""
    video_path = Config.TEMP_DIR / f"bg_{uuid.uuid4()}.mp4"
    try:
        api = API(Config.get_api_key("PEXELS_API_KEY"))
        api.search_videos(query, page=1, results_per_page=10)
        
        videos = [v for v in api.videos if v['duration'] >= Config.VIDEO_DURATION]
        if videos:
            video = random.choice(videos)
            video_url = video['video_files'][0]['link']
            
            with requests.get(video_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(video_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return video_path
        else:
            raise ValueError("적합한 영상 없음")
    except Exception as e:
        logger.warning(f"Pexels 실패: {e}, 단색 배경 생성")
        try:
            color = f"{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
            subprocess.run([
                'ffmpeg', '-f', 'lavfi',
                '-i', f'color=c={color}:r=24:d={Config.VIDEO_DURATION}:s={Config.SHORTS_WIDTH}x{Config.SHORTS_HEIGHT}',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                '-y', str(video_path)
            ], check=True)
            return video_path
        except Exception as e:
            logger.error(f"배경 생성 실패: {e}")
            raise
