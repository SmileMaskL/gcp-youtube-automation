# src/bg_downloader.py (새 파일 또는 기존 파일 수정)
import logging
import requests
import os
import random

logger = logging.getLogger(__name__)

# Pexels API 문서: https://www.pexels.com/api/documentation/#videos
# API 키 필요

class BackgroundDownloader:
    def __init__(self, api_key: str):
        if not api_key:
            logger.error("Pexels API Key is not provided.")
            raise ValueError("Pexels API Key is missing.")
        self.api_key = api_key
        self.base_url = "https://api.pexels.com/videos"

    def search_videos(self, query: str, per_page: int = 10) -> list:
        """
        Pexels API를 사용하여 비디오를 검색합니다.
        
        Args:
            query (str): 검색어.
            per_page (int): 페이지당 결과 수.

        Returns:
            list: 검색된 비디오 URL 목록.
        """
        headers = {"Authorization": self.api_key}
        params = {"query": query, "per_page": per_page}
        try:
            response = requests.get(f"{self.base_url}/search", headers=headers, params=params)
            response.raise_for_status() # HTTP 오류 발생 시 예외 발생
            data = response.json()
            
            video_urls = []
            for video_item in data.get('videos', []):
                # 가장 높은 해상도의 비디오 파일을 찾기
                max_quality_url = None
                max_quality_res = 0
                for file_info in video_item.get('video_files', []):
                    # 'link' 필드를 사용 (Pexels API 변경될 수 있음)
                    # 'quality' 필드가 있다면 사용, 없으면 'width'나 'height'로 판단
                    quality = file_info.get('quality')
                    if quality == 'hd' or quality == 'sd': # 예시: 'hd' 선호
                        video_urls.append(file_info['link'])
                        break # 첫 번째 HD 또는 SD 비디오를 사용
                    
                    # 해상도로 판단
                    if 'width' in file_info and 'height' in file_info:
                        current_res = file_info['width'] * file_info['height']
                        if current_res > max_quality_res:
                            max_quality_res = current_res
                            max_quality_url = file_info['link']
                if max_quality_url:
                    video_urls.append(max_quality_url)
            
            logger.info(f"Found {len(video_urls)} videos for query '{query}' from Pexels.")
            return video_urls
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching Pexels videos for query '{query}': {e}")
            return []

    def download_video(self, video_url: str, output_path: str) -> bool:
        """
        주어진 URL에서 비디오 파일을 다운로드합니다.
        """
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Video downloaded successfully to {output_path}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading video from {video_url}: {e}")
            return False

# main.py에서 사용 예시:
# from src.bg_downloader import BackgroundDownloader
# ...
# bg_downloader = BackgroundDownloader(api_key=config.pexels_api_key)
# video_urls = bg_downloader.search_videos(query=topic, per_page=5)
# if video_urls:
#    selected_video_url = random.choice(video_urls)
#    background_video_path = os.path.join("/tmp", f"bg_{uuid.uuid4().hex}.mp4")
#    if bg_downloader.download_video(selected_video_url, background_video_path):
#        video_success = video_creator.create_video(..., background_video_path=background_video_path)
#    else:
#        background_video_path = None # 다운로드 실패 시 배경 비디오 없이 진행
# else:
#    background_video_path = None
#
# 그리고 VideoCreator.create_video 함수에서 background_video_path를 활용하도록 수정해야 합니다.
