# src/config.py

import os
from google.cloud import secretmanager
import logging

logger = logging.getLogger(__name__)
# Cloud Function은 INFO 레벨 로그도 기본적으로 Cloud Logging에 수집합니다.
# 하지만 더 자세한 디버깅을 위해 DEBUG 레벨로 일시적으로 변경할 수 있습니다.
logging.basicConfig(level=logging.DEBUG)

class Config:
    def __init__(self):
        logger.info("Config 초기화 시작...")
        
        # 환경 변수 로드
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
        self.gcp_bucket_name = os.getenv("GCP_BUCKET_NAME")
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID")

        if not self.gcp_project_id:
            logger.critical("환경 변수 GCP_PROJECT_ID가 설정되지 않았습니다.")
            raise ValueError("GCP_PROJECT_ID 환경 변수가 필요합니다.")
        if not self.gcp_bucket_name:
            logger.critical("환경 변수 GCP_BUCKET_NAME이 설정되지 않았습니다.")
            raise ValueError("GCP_BUCKET_NAME 환경 변수가 필요합니다.")
        if not self.elevenlabs_voice_id:
            logger.critical("환경 변수 ELEVENLABS_VOICE_ID가 설정되지 않았습니다.")
            raise ValueError("ELEVENLABS_VOICE_ID 환경 변수가 필요합니다.")

        logger.info(f"GCP_PROJECT_ID: {self.gcp_project_id}")
        logger.info(f"GCP_BUCKET_NAME: {self.gcp_bucket_name}")
        logger.info(f"ELEVENLABS_VOICE_ID: {self.elevenlabs_voice_id}")


        # Secret Manager 클라이언트 초기화 및 시크릿 값 가져오기
        try:
            logger.info("Secret Manager 클라이언트 초기화 시도...")
            self.secret_manager_client = secretmanager.SecretManagerServiceClient()
            logger.info("Secret Manager 클라이언트 초기화 성공.")

            # ---- 여기를 수정해야 합니다! Secret Manager의 실제 시크릿 이름과 일치시키세요. ----
            # Secret Manager 콘솔에서 실제 시크릿 이름 확인 후 소문자/하이픈 여부 확인
            # Secret Manager에 "youtube-client-id" 로 저장되어 있다면:
            self.youtube_client_id_secret_name = self.secret_manager_client.secret_path(self.gcp_project_id, "youtube-client-id")
            self.youtube_client_secret_secret_name = self.secret_manager_client.secret_path(self.gcp_project_id, "youtube-client-secret")
            self.youtube_refresh_token_secret_name = self.secret_manager_client.secret_path(self.gcp_project_id, "youtube-refresh-token")
            
            # ELEVENLABS_API_KEY도 Secret Manager에 "elevenlabs-api-key" 로 저장되어 있다면:
            self.elevenlabs_api_key_secret_name = self.secret_manager_client.secret_path(self.gcp_project_id, "elevenlabs-api-key")
            # 만약 Secret Manager에 "ELEVENLABS_API_KEY" 그대로 저장되어 있다면 위 줄은 수정하지 않아도 됩니다.
            # 하지만 대부분의 GCP Secret Manager 권장 명명 규칙은 소문자-하이픈입니다.
            # ----------------------------------------------------------------------------------

            # 디버깅을 위해 Config 초기화 시점에 시크릿을 직접 가져와보는 코드 추가 (임시)
            # 이 코드는 초기화 실패의 원인을 Secret Manager 접근 오류로 빠르게 좁힐 수 있게 해줍니다.
            logger.debug("Config 초기화 중 시크릿 값 테스트 로드 시작...")
            try:
                test_yt_client_id = self.get_youtube_client_id()
                logger.debug(f"YOUTUBE_CLIENT_ID 테스트 로드 성공: {test_yt_client_id[:5]}...")
            except Exception as e:
                logger.critical(f"Config 초기화 중 YOUTUBE_CLIENT_ID 로드 실패: {e}", exc_info=True)
                raise # 오류를 다시 발생시켜 컨테이너 종료 원인으로 지목

            try:
                test_elevenlabs_key = self.get_elevenlabs_api_key()
                logger.debug(f"ELEVENLABS_API_KEY 테스트 로드 성공: {test_elevenlabs_key[:5]}...")
            except Exception as e:
                logger.critical(f"Config 초기화 중 ELEVENLABS_API_KEY 로드 실패: {e}", exc_info=True)
                raise # 오류를 다시 발생시켜 컨테이너 종료 원인으로 지목
            logger.debug("Config 초기화 중 시크릿 값 테스트 로드 완료.")


        except Exception as e:
            logger.critical(f"Config 초기화 중 Secret Manager 관련 치명적인 오류 발생: {e}", exc_info=True)
            raise RuntimeError(f"Secret Manager 초기화 실패: {e}") 

        logger.info("Config 초기화 완료.")

    # ... (기존 게터 메서드들은 그대로 유지) ...
    # get_youtube_client_id, get_youtube_client_secret, get_youtube_refresh_token, get_elevenlabs_api_key
    # 이 게터 메서드들은 Secret Manager에서 값을 가져올 때 다시 사용되므로,
    # 위에서 secret_path에 설정한 이름과 이 게터 메서드가 참조하는 이름이 일치해야 합니다.
