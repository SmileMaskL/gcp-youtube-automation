import logging
import requests
import random

logger = logging.getLogger(__name__)

PEXELS_API_BASE_URL = "https://api.pexels.com/videos"
PEXELS_SEARCH_ENDPOINT = "/search"

def download_background_video(pexels_api_key, query, output_path, min_duration=5, max_duration=60):
    headers = {"Authorization": pexels_api_key}
    params = {
        "query": query,
        "per_page": 15,
        "orientation": "portrait",
        "min_duration": min_duration,
        "max_duration": max_duration
    }

    try:
        logger.info(f"Pexels에서 배경 영상 검색 시작. 쿼리: '{query}'")
        response = requests.get(f"{PEXELS_API_BASE_URL}{PEXELS_SEARCH_ENDPOINT}", headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        videos = data.get("videos", [])
        if not videos:
            logger.warning(f"'{query}'에 대한 Pexels 영상 검색 결과가 없습니다.")
            raise ValueError(f"Pexels에서 '{query}'에 대한 영상을 찾을 수 없습니다.")

        selected_video = random.choice(videos)
        video_url = None
        
        if selected_video.get("video_files"):
            for vf in selected_video["video_files"]:
                if (vf.get("quality") == "hd" and 
                    vf.get("width") and 
                    vf.get("height") and 
                    vf["height"] > vf["width"]):
                    video_url = vf["link"]
                    break
            if not video_url:
                video_url = selected_video["video_files"][0]["link"]
        
        if not video_url:
            raise ValueError("선택된 비디오에서 유효한 다운로드 URL을 찾을 수 없습니다.")

        logger.info(f"선택된 배경 영상 다운로드 시작: {video_url}")
        video_response = requests.get(video_url, stream=True)
        video_response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"배경 영상 다운로드 완료: {output_path}")
        return output_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Pexels API 요청 실패 또는 네트워크 오류: {e}", exc_info=True)
        raise
    except ValueError as e:
        logger.error(f"Pexels 영상 처리 오류: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"알 수 없는 배경 영상 다운로드 오류: {e}", exc_info=True)
        raise
