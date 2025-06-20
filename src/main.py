import logging
import os
import json
import random
import time
from google.cloud import secretmanager
from src.video_creator import create_video

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# OpenAI API 키 로테이션 클래스 (예시)
class OpenAIKeyRotator:
    def __init__(self, keys):
        self.keys = keys
        self.index = 0

    def get_key(self):
        key = self.keys[self.index]
        self.index = (self.index + 1) % len(self.keys)
        return key

def access_secret(secret_id: str, version: str = "latest") -> str:
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise RuntimeError("GCP_PROJECT_ID 환경변수가 없습니다.")
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def main():
    logging.info("프로그램 시작")

    # 1. 환경변수에서 OpenAI 키 JSON 문자열 읽어오기 및 파싱
    openai_keys_json = os.getenv("OPENAI_KEYS_JSON")
    if not openai_keys_json:
        logging.error("OPENAI_KEYS_JSON 환경변수가 없습니다.")
        return
    openai_keys = json.loads(openai_keys_json)
    key_rotator = OpenAIKeyRotator(openai_keys)

    # 2. 매일 5개 영상 자동 생성 예시
    for i in range(5):
        try:
            # 매번 로테이션 된 API 키 할당 (예: OpenAI 사용 시)
            current_api_key = key_rotator.get_key()
            os.environ["OPENAI_API_KEY"] = current_api_key
            logging.info(f"OpenAI API 키 할당: {current_api_key[:6]}...")

            # 콘텐츠 텍스트 (핫이슈 또는 뉴스 API 연동하여 텍스트 자동 생성 가능)
            # 여기서는 간단 예시로 고정 텍스트 사용
            video_text = f"자동화 테스트 영상 #{i+1}: 오늘의 핫이슈와 정보를 알려드립니다."

            # 영상 생성 및 저장
            output_path = f"output/final_video_{i+1}.mp4"
            create_video(video_text, output_path=output_path)

            # TODO: 여기에 YouTube API를 이용한 업로드 코드 삽입 (아래 참고)

            time.sleep(5)  # API 쿼터 고려하여 잠시 대기
        except Exception as e:
            logging.error(f"영상 생성/업로드 중 오류: {e}")

    logging.info("프로그램 정상 종료")

if __name__ == "__main__":
    main()
