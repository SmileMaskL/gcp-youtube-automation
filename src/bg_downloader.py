    # src/bg_downloader.py

    import logging
    import requests
    import os
    import random

    logger = logging.getLogger(__name__)

    # Pexels API Base URL 및 Endpoint
    PEXELS_API_BASE_URL = "[https://api.pexels.com/videos](https://api.pexels.com/videos)"
    PEXELS_SEARCH_ENDPOINT = "/search"

    def download_background_video(pexels_api_key, query, output_path, min_duration=5, max_duration=60):
        """
        Pexels API를 사용하여 쿼리에 해당하는 배경 영상을 다운로드합니다.
        
        Args:
            pexels_api_key (str): Pexels API 키.
            query (str): 검색 쿼리 (예: "nature", "city", "technology").
            output_path (str): 다운로드된 비디오 파일을 저장할 경로.
            min_duration (int): 최소 비디오 길이 (초).
            max_duration (int): 최대 비디오 길이 (초).
        Returns:
            str: 다운로드된 비디오 파일의 경로.
        """
        headers = {
            "Authorization": pexels_api_key
        }
        params = {
            "query": query,
            "per_page": 15, # 한 페이지당 결과 수
            "orientation": "portrait", # 세로형 영상 (쇼츠에 적합)
            "min_duration": min_duration,
            "max_duration": max_duration
        }

        try:
            logger.info(f"Pexels에서 배경 영상 검색 시작. 쿼리: '{query}'")
            response = requests.get(f"{PEXELS_API_BASE_URL}{PEXELS_SEARCH_ENDPOINT}", headers=headers, params=params)
            response.raise_for_status() # HTTP 오류 발생 시 예외 발생
            data = response.json()

            videos = data.get("videos", [])
            if not videos:
                logger.warning(f"'{query}'에 대한 Pexels 영상 검색 결과가 없습니다. 다른 쿼리를 시도하거나 기본 영상 사용을 고려하세요.")
                raise ValueError(f"Pexels에서 '{query}'에 대한 영상을 찾을 수 없습니다.")

            # 여러 비디오 중 무작위로 하나 선택
            selected_video = random.choice(videos)
            
            # 비디오 파일의 다양한 해상도 중 가장 적합한 것 선택 (예: 'sd' 또는 'hd' 또는 'medium')
            # Pexels API 응답 구조를 확인하여 가장 적합한 'link'를 선택해야 합니다.
            # 일반적으로 video_files 리스트에 해상도별 링크가 있습니다.
            video_url = None
            # 가장 높은 해상도의 세로형 비디오를 찾거나, 'hd' 또는 'sd' 중 하나를 선택
            # Pexels 응답 형식에 따라 이 로직은 달라질 수 있습니다.
            # 여기서는 편의상 첫 번째 'link'를 사용한다고 가정합니다.
            if selected_video.get("video_files"):
                # 보통 가장 높은 해상도 (width, height) 또는 특정 퀄리티 ('hd', 'sd')를 선택합니다.
                # 여기서는 단순히 첫 번째 사용 가능한 링크를 가져옵니다. 실제로는 더 정교한 로직이 필요.
                for vf in selected_video["video_files"]:
                    if vf.get("quality") == "hd" and vf.get("width") and vf.get("height") and vf["height"] > vf["width"]: # 세로형 HD
                        video_url = vf["link"]
                        break
                if not video_url: # HD 세로형이 없으면 그냥 첫 번째 링크 사용
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
    
