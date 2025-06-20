import logging
import os
import json
import random
import time
from google.cloud import secretmanager
from src.video_creator import create_video

# ✅ 로깅 기본 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ✅ OpenAI API 키 로테이터 클래스
class OpenAIKeyRotator:
    def __init__(self, keys):
        if not keys:
            raise ValueError("OpenAI 키 목록이 비어 있습니다.")
        self.keys = keys
        self.index = 0

    def get_key(self):
        key = self.keys[self.index]
        self.index = (self.index + 1) % len(self.keys)
        return key

# ✅ GCP Secret Manager에서 시크릿 가져오기
def access_secret(secret_id: str, version: str = "latest") -> str:
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            raise RuntimeError("❌ GCP_PROJECT_ID 환경변수가 없습니다.")
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logging.error(f"❌ SecretManager 접근 실패: {e}")
        raise

# ✅ 메인 로직
def main():
    logging.info("🚀 프로그램 시작")

    # 1. OpenAI 키 리스트 파싱
    openai_keys_json = os.getenv("OPENAI_KEYS_JSON")
    if not openai_keys_json:
        logging.error("❌ OPENAI_KEYS_JSON 환경변수가 없습니다.")
        return

    try:
        openai_keys = json.loads(openai_keys_json)
        key_rotator = OpenAIKeyRotator(openai_keys)
    except Exception as e:
        logging.error(f"❌ OpenAI 키 파싱 실패: {e}")
        return

    # 2. 테스트 영상 예제 1개 생성 (추가 요청한 부분)
    try:
        logging.info("🎬 [예제] 단일 테스트 영상 생성")
        test_output = create_video("이것은 AI가 자동으로 만든 유튜브 영상입니다.", output_path="output/test_video.mp4")
        logging.info(f"✅ 테스트 영상 생성 완료: {test_output}")
    except Exception as e:
        logging.error(f"❌ 테스트 영상 생성 실패: {e}")

    # 3. 반복 영상 생성 (예: 매일 5개 자동 생성)
    for i in range(5):
        try:
            current_api_key = key_rotator.get_key()
            os.environ["OPENAI_API_KEY"] = current_api_key
            logging.info(f"🔑 OpenAI API 키 할당: {current_api_key[:6]}...")

            # 간단한 텍스트 기반 자동 콘텐츠 (향후 Gemini API 연동 가능)
            video_text = f"자동화 테스트 영상 #{i+1}: 오늘의 핫이슈와 정보를 알려드립니다."

            output_path = f"output/final_video_{i+1}.mp4"
            result = create_video(video_text, output_path=output_path)

            # 🔄 TODO: YouTube API로 result 업로드
            logging.info(f"📤 영상 저장 완료: {result}")

            time.sleep(5)  # API 쿼터 회피용 대기

        except Exception as e:
            logging.error(f"❌ 영상 생성/업로드 중 오류 발생: {e}")

    logging.info("✅ 전체 영상 생성 프로세스 완료")

# ✅ 스크립트 직접 실행
if __name__ == "__main__":
    main()
