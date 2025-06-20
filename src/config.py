from src.config import get_secret
import os
import json
import logging
from typing import Optional, Union, Dict, List
from google.cloud import secretmanager
from google.api_core.exceptions import NotFound, PermissionDenied

def get_secret(secret_name: str, version: str = "latest") -> str:
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise ValueError("GCP_PROJECT_ID 환경 변수가 설정되지 않았습니다.")
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/{version}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# 로거 설정
logger = logging.getLogger(__name__)

def setup_logging(log_file: Optional[str] = None, debug: bool = False) -> None:
    """
    로깅 설정을 초기화합니다. Cloud Run 환경과 로컬 개발 환경 모두에서 작동하도록 설계되었습니다.
    
    Args:
        log_file (str, optional): 로그를 저장할 파일 경로. None이면 콘솔에만 출력.
        debug (bool): True로 설정하면 DEBUG 레벨 로깅을 활성화합니다.
    """
    log_level = logging.DEBUG if debug else logging.INFO
    handlers = [logging.StreamHandler()]
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    # GCP 관련 로그는 WARNING 레벨 이상만 출력
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

class SecretManager:
    """
    Google Secret Manager와 상호작용을 위한 래퍼 클래스.
    로컬 개발과 프로덕션 환경 모두에서 작동하도록 설계되었습니다.
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Args:
            project_id (str, optional): GCP 프로젝트 ID. None이면 환경 변수에서 읽음.
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID 환경 변수가 설정되지 않았습니다.")
        
        self.client = secretmanager.SecretManagerServiceClient()
        logger.info(f"SecretManager initialized for project: {self.project_id}")

    def get_secret(self, secret_name: str, version: str = "latest") -> str:
        """
        Secret Manager에서 시크릿 값을 가져옵니다.
        
        Args:
            secret_name (str): Secret Manager에 저장된 시크릿의 ID
            version (str): 시크릿 버전 (기본값: "latest")
            
        Returns:
            str: 시크릿 값
            
        Raises:
            ValueError: 시크릿을 찾을 수 없거나 접근 권한이 없는 경우
            RuntimeError: 기타 오류 발생 시
        """
        name = f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"
        
        try:
            response = self.client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")
            logger.info(f"Successfully retrieved secret: {secret_name}")
            return secret_value
        except NotFound:
            error_msg = f"시크릿을 찾을 수 없습니다: {secret_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except PermissionDenied:
            error_msg = f"시크릿에 접근할 권한이 없습니다: {secret_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"시크릿을 가져오는 중 오류 발생: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)

    def get_json_secret(self, secret_name: str) -> Union[Dict, List]:
        """
        JSON 형식으로 저장된 시크릿을 파싱하여 가져옵니다.
        
        Args:
            secret_name (str): Secret Manager에 저장된 시크릿의 ID
            
        Returns:
            Union[Dict, List]: 파싱된 JSON 데이터
            
        Raises:
            ValueError: JSON 파싱 실패 시
        """
        secret_value = self.get_secret(secret_name)
        try:
            return json.loads(secret_value)
        except json.JSONDecodeError as e:
            error_msg = f"시크릿 JSON 파싱 실패: {secret_name} - {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

def load_config() -> Dict:
    """
    애플리케이션 구성을 로드합니다. 환경 변수와 Secret Manager를 모두 확인합니다.
    
    Returns:
        Dict: 로드된 구성 딕셔너리
        
    Raises:
        ValueError: 필수 구성이 누락된 경우
    """
    config = {}
    secret_manager = SecretManager()
    
    try:
        # 필수 시크릿 로드
        config["ELEVENLABS_API_KEY"] = secret_manager.get_secret("ELEVENLABS_API_KEY")
        config["ELEVENLABS_VOICE_ID"] = os.getenv("ELEVENLABS_VOICE_ID", "uyVNoMrnUku1dZyVEXwD")
        config["OPENAI_KEYS"] = secret_manager.get_json_secret("OPENAI_KEYS_JSON")
        config["GEMINI_API_KEY"] = secret_manager.get_secret("GEMINI_API_KEY")
        config["YOUTUBE_OAUTH_CREDENTIALS"] = secret_manager.get_secret("YOUTUBE_OAUTH_CREDENTIALS")
        config["PEXELS_API_KEY"] = secret_manager.get_secret("PEXELS_API_KEY")
        
        # 선택적 환경 변수
        config["FONT_PATH"] = os.getenv("FONT_PATH", "./fonts/Catfont.ttf")
        config["OUTPUT_DIR"] = os.getenv("OUTPUT_DIR", "./output")
        config["LOG_DIR"] = os.getenv("LOG_DIR", "./logs")
        config["MAX_RETRIES"] = int(os.getenv("MAX_RETRIES", "3"))
        
        logger.info("성공적으로 모든 구성을 로드했습니다.")
        return config
        
    except Exception as e:
        logger.error(f"구성 로드 중 오류 발생: {str(e)}", exc_info=True)
        raise ValueError(f"구성 로드 실패: {str(e)}")

# 전역 로깅 설정 (기본값)
setup_logging()

if __name__ == "__main__":
    # 로컬 테스트를 위한 환경 변수 로드
    from dotenv import load_dotenv
    load_dotenv()
    
    # 테스트 실행
    try:
        print("=== 시크릿 매니저 테스트 시작 ===")
        
        # 테스트용 구성 로드
        test_config = load_config()
        print(f"로드된 구성 키: {list(test_config.keys())}")
        
        # 민감한 정보는 일부만 표시
        print(f"ElevenLabs API Key (첫 5자): {test_config['ELEVENLABS_API_KEY'][:5]}*****")
        print(f"OpenAI Keys 개수: {len(test_config['OPENAI_KEYS']) if isinstance(test_config['OPENAI_KEYS'], list) else 1}")
        print(f"Gemini API Key (첫 5자): {test_config['GEMINI_API_KEY'][:5]}*****")
        print(f"폰트 경로: {test_config['FONT_PATH']}")
        print(f"출력 디렉토리: {test_config['OUTPUT_DIR']}")
        
        print("=== 테스트 성공 ===")
        
    except Exception as e:
        print(f"!!! 테스트 실패: {str(e)}")
        logger.exception("테스트 중 예외 발생")
