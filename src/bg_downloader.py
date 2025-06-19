import requests
import os
import random
import logging

logger = logging.getLogger(__name__)

def download_background_video(query: str, output_path: str, api_key: str, min_duration=55, max_duration=65):
    """
    Pexels API를 사용하여 지정된 쿼리의 무료 배경 비디오를 다운로드합니다.
    YouTube Shorts에 적합하도록 55~65초 길이의 영상을 선호합니다.
    Args:
        query (str): 검색할 키워드.
        output_path (str): 비디오를 저장할 경로.
        api_key (str): Pexels API 키.
        min_duration (int): 최소 비디오 길이 (초).
        max_duration (int): 최대 비디오 길이 (초).
    """
    if not api_key:
        logger.error("Pexels API Key is not provided.")
        raise ValueError("Pexels API Key is missing.")

    headers = {
        "Authorization": api_key
    }
    # Pexels 비디오 검색 API 엔드포인트
    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=15"

    try:
        response = requests.get(url, headers=headers, timeout=15) # 15초 타임아웃
        response.raise_for_status()
        data = response.json()

        videos = data.get('videos', [])
        if not videos:
            logger.warning(f"No videos found for query: {query}. Trying a more general query.")
            # 더 일반적인 쿼리로 재시도
            if " " in query:
                return download_background_video(query.split(' ')[0], output_path, api_key, min_duration, max_duration)
            else:
                return download_background_video("nature", output_path, api_key, min_duration, max_duration) # 기본값

        # 길이 조건에 맞는 비디오 필터링 및 무작위 선택
        suitable_videos = [
            v for v in videos
            if min_duration <= v.get('duration', 0) <= max_duration
        ]

        if not suitable_videos:
            logger.warning(f"No videos found within duration {min_duration}-{max_duration}s for query: {query}. Using any available video.")
            # 길이 조건에 맞는 영상이 없으면 아무 영상이나 선택
            suitable_videos = videos

        selected_video = random.choice(suitable_videos)

        # 가장 해상도가 높은 비디오 파일 URL 찾기
        video_files = selected_video.get('video_files', [])
        # 'sd' (standard definition) 또는 'hd' (high definition) 중 적절한 해상도 선택
        # 여기서는 기본적으로 가장 큰 해상도를 찾지만, Shorts는 FHD면 충분
        video_url = None
        
        # 'sd', 'hd', 'fhd', '4k' 등 원하는 품질 순서로 찾을 수 있음.
        # 여기서는 가장 해상도가 높은 파일을 선택하도록 합니다.
        # 또는 'link' 유형의 비디오가 직접 다운로드 가능한 URL을 포함하는 경우가 많음.
        
        # 'link' 타입 또는 'video/mp4' 타입의 고해상도 파일을 우선적으로 찾음
        best_quality_url = None
        for file in video_files:
            if file.get('file_type') == 'video/mp4':
                if not best_quality_url or file.get('width', 0) * file.get('height', 0) > best_quality_url.get('width', 0) * best_quality_url.get('height', 0):
                    best_quality_url = file
        
        if best_quality_url:
            video_url = best_quality_url['link']
        
        if not video_url:
            logger.error(f"No suitable video file URL found for selected video {selected_video.get('id')}.")
            raise ValueError("No suitable video file URL found.")


        # 출력 디렉토리 확인 및 생성
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 비디오 다운로드
        with requests.get(video_url, stream=True, timeout=30) as r: # 30초 타임아웃
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info(f"Background video downloaded successfully to {output_path}")
        
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while downloading video: {http_err} - {response.text}")
        raise
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error occurred while downloading video: {conn_err}")
        raise
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error occurred while downloading video: {timeout_err}")
        raise
    except requests.exceptions.RequestException as req_err:
        logger.error(f"An error occurred during video download: {req_err}")
        raise
    except json.JSONDecodeError as json_err:
        logger.error(f"JSON decoding error from Pexels API: {json_err} - Response text: {response.text}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred in download_background_video: {e}", exc_info=True)
        raise
