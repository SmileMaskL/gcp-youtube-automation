from pexels.client import Client
import requests
import os
from pathlib import Path
from src.config import PEXELS_API_KEY, BACKGROUND_IMAGE_DIR, MAX_PEXELS_CALLS_PER_DAY
from src.monitoring import log_system_health
from src.usage_tracker import api_usage_tracker

def download_background(keyword="nature", output_filename="background.jpg"):
    """
    Pexels API를 사용하여 배경 이미지를 다운로드합니다.
    키워드에 따라 관련 이미지를 찾습니다.
    """
    if not api_usage_tracker.check_limit("pexels", api_usage_tracker.get_usage("pexels"), MAX_PEXELS_CALLS_PER_DAY):
        log_system_health("Pexels API 일일 사용 한도 초과. 기본 배경 이미지 사용 또는 다음 실행 시도.", level="warning")
        # 대안으로 로컬에 저장된 기본 이미지 경로를 반환하거나 에러를 발생시킬 수 있습니다.
        # 여기서는 에러를 발생시켜 워크플로우를 중단합니다.
        raise ValueError("Pexels API 한도 초과. 배경 이미지를 다운로드할 수 없습니다.")

    if not PEXELS_API_KEY:
        log_system_health("Pexels API Key가 설정되지 않았습니다.", level="error")
        raise ValueError("Pexels API Key가 설정되지 않았습니다. 배경 이미지를 다운로드할 수 없습니다.")

    client = Client(api_key=PEXELS_API_KEY)

    # 'orientation'을 'landscape'로 지정하여 가로형 이미지를 선호
    try:
        response = client.photos.search(query=keyword, orientation='landscape', per_page=1)
    except Exception as e:
        log_system_health(f"Pexels API 호출 오류: {e}", level="error")
        raise ValueError(f"Pexels API 호출 중 오류 발생: {e}")

    api_usage_tracker.record_usage("pexels")

    if response and response.get("photos"):
        photo_url = response["photos"][0]["src"]["original"]
        output_path = os.path.join(BACKGROUND_IMAGE_DIR, output_filename)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            img_data = requests.get(photo_url, stream=True)
            img_data.raise_for_status() # HTTP 오류가 발생하면 예외 발생

            with open(output_path, "wb") as f:
                for chunk in img_data.iter_content(chunk_size=8192):
                    f.write(chunk)
            log_system_health(f"배경 이미지가 성공적으로 다운로드되었습니다: {output_path}", level="info")
            return output_path
        except requests.exceptions.RequestException as e:
            log_system_health(f"이미지 다운로드 중 오류 발생: {e}", level="error")
            raise ValueError(f"배경 이미지 다운로드 실패: {e}")
    else:
        log_system_health(f"키워드 '{keyword}'에 대한 배경 이미지를 찾을 수 없습니다.", level="warning")
        raise ValueError(f"키워드 '{keyword}'에 대한 배경 이미지를 찾을 수 없습니다.")
