import os
import requests
import logging
from pexels.client import Client
from typing import Optional
from pathlib import Path
from src.config import Config # 수정

logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self):
        self.api_key = Config.get_pexels_api_key() # 수정: Config에서 Pexels API 키 가져오기
        if not self.api_key:
            raise ValueError("PEXELS_API_KEY가 설정되지 않았습니다.")
        self.base_url = "https://api.pexels.com/videos/search"
        
    def download_video(self, query: str) -> Optional[str]:
        try:
            headers = {"Authorization": self.api_key}
            params = {
                "query": query + " background",
                "per_page": 3, # 적절한 수의 결과 요청 (과도한 API 사용 방지)
                "orientation": "portrait", # 쇼츠에 적합한 세로 방향 영상
                "size": "small" # 작은 크기의 영상 선호
            }
            
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status() # HTTP 오류 발생 시 예외 발생
            
            videos = response.json().get('videos', [])
            if not videos:
                logger.warning(f"검색 결과 없음: {query}")
                return None
            
            # 가장 작은 크기보다는 쇼츠에 적합한 해상도 (예: 720x1280)를 찾아 다운로드
            # Pexels API 응답의 'video_files' 배열에서 'height'가 1280에 가까운 영상 선택
            best_video_file = None
            min_diff = float('inf')
            
            for video_data in videos[0]['video_files']:
                if video_data.get('height') and video_data.get('width'):
                    # 9:16 비율에 가장 가까운 영상 선호
                    aspect_ratio = video_data['width'] / video_data['height']
                    if 0.5 <= aspect_ratio <= 0.6: # 대략 9:16 비율 (0.5625)
                        diff = abs(video_data['height'] - 1280)
                        if diff < min_diff:
                            min_diff = diff
                            best_video_file = video_data['link']
            
            if not best_video_file:
                # 적합한 영상이 없으면 기본적으로 가장 작은 크기의 세로 영상 선택
                portrait_videos = [v for v in videos[0]['video_files'] if v.get('height', 0) > v.get('width', 0)]
                if portrait_videos:
                    best_video_file = min(portrait_videos, key=lambda x: x.get('size', float('inf')))['link']
                else:
                    best_video_file = min(videos[0]['video_files'], key=lambda x: x.get('size', float('inf')))['link'] # 세로 영상이 없으면 전체에서 가장 작은 것
            
            os.makedirs("temp", exist_ok=True)
            # 파일 이름에 특수 문자 방지 및 고유성 확보
            clean_query = ''.join(c if c.isalnum() else '_' for c in query)
            timestamp = int(datetime.now().timestamp())
            video_path = f"temp/bg_{clean_query}_{timestamp}.mp4"
            
            logger.info(f"배경 영상 다운로드 시작: {best_video_file}")
            with requests.get(best_video_file, stream=True, timeout=30) as r: # 다운로드 타임아웃 30초로 늘림
                r.raise_for_status()
                with open(video_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            logger.info(f"배경 영상 다운로드 성공: {video_path}")
            return video_path
            
        except requests.exceptions.RequestException as req_e:
            logger.error(f"Pexels API 요청 실패 ({query}): {req_e}")
            return None
        except Exception as e:
            logger.error(f"비디오 다운로드 실패 ({query}): {str(e)}", exc_info=True)
            return None

def download_background(query: str) -> Optional[str]:
    downloader = VideoDownloader()
    for attempt in range(3): # 최대 3번 재시도
        video_path = downloader.download_video(query)
        if video_path:
            return video_path
        logger.warning(f"'{query}'에 대한 배경 영상 다운로드 재시도 {attempt + 1}/3")
        time.sleep(2 ** attempt) # 지수 백오프
    
    logger.error(f"'{query}'에 대한 배경 영상을 찾을 수 없습니다. 모든 재시도 실패.")
    return None # 배경 영상 다운로드 실패 시 None 반환
