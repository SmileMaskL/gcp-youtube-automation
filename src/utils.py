"""
유틸리티 함수들 (수정 완료 버전)
"""
import os
from elevenlabs.client import ElevenLabs
import uuid
import tempfile
import json
import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileManager:
    """파일 관리 유틸리티"""
    
    @staticmethod
    def ensure_dir(path: str) -> None:
        """디렉터리가 없으면 생성"""
        Path(path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """파일명에서 특수문자 제거"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:255]
    
    @staticmethod
    def get_file_hash(filepath: str) -> str:
        """파일의 MD5 해시값 반환"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"파일 해시 계산 실패: {e}")
            return ""
    
    @staticmethod
    def get_file_size(filepath: str) -> int:
        """파일 크기 반환 (bytes)"""
        try:
            return os.path.getsize(filepath)
        except Exception:
            return 0

def text_to_speech(text: str) -> str:
    """텍스트를 음성으로 변환 (수정된 버전)"""
    try:
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        audio = client.generate(
            text=text,
            voice="Rachel",
            model="eleven_multilingual_v2"
        )
        
        temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp3")
        with open(temp_path, "wb") as f:
            f.write(audio)
        
        return temp_path
    except Exception as e:
        logger.error(f"음성 생성 실패: {e}")
        raise

class ConfigManager:
    """설정 관리 유틸리티"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return self.get_default_config()
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            return self.get_default_config()
    
    def save_config(self) -> None:
        """설정 파일 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"설정 파일 저장 실패: {e}")
    
    def get_default_config(self) -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            "video": {
                "resolution": "1920x1080",
                "fps": 30,
                "bitrate": "5000k",
                "format": "mp4"
            },
            "audio": {
                "bitrate": "128k",
                "sample_rate": 44100
            },
            "upload": {
                "auto_upload": True,
                "privacy": "unlisted",
                "category": "22"  # People & Blogs
            },
            "cleanup": {
                "auto_cleanup": True,
                "max_age_days": 7,
                "max_size_gb": 3
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정값 가져오기"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """설정값 설정하기"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()

class RateLimiter:
    """API 호출 제한 관리"""
    
    def __init__(self, max_calls: int = 60, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_make_call(self) -> bool:
        """호출 가능 여부 확인"""
        now = time.time()
        # 시간 윈도우 내의 호출만 유지
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.time_window]
        return len(self.calls) < self.max_calls
    
    def make_call(self) -> None:
        """호출 기록"""
        if self.can_make_call():
            self.calls.append(time.time())
        else:
            raise Exception("Rate limit exceeded")
    
    def wait_time(self) -> float:
        """다음 호출까지의 대기 시간"""
        if self.can_make_call():
            return 0
        
        now = time.time()
        oldest_call = min(self.calls)
        return self.time_window - (now - oldest_call)

class APIClient:
    """API 클라이언트 기본 클래스"""
    
    def __init__(self, base_url: str, api_key: str = None, rate_limit: RateLimiter = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.rate_limiter = rate_limit or RateLimiter()
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """API 요청 실행"""
        # Rate limiting
        if not self.rate_limiter.can_make_call():
            wait_time = self.rate_limiter.wait_time()
            logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
            time.sleep(wait_time)
        
        self.rate_limiter.make_call()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API 요청 실패: {e}")
            raise

class CacheManager:
    """캐시 관리 유틸리티"""
    
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_path(self, key: str) -> Path:
        """캐시 파일 경로 생성"""
        # 키를 안전한 파일명으로 변환
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.json"
    
    def get(self, key: str, max_age: int = 3600) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        cache_file = self.get_cache_path(key)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 캐시 만료 확인
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time > timedelta(seconds=max_age):
                cache_file.unlink()  # 만료된 캐시 삭제
                return None
            
            return cache_data['data']
        except Exception as e:
            logger.error(f"캐시 조회 실패: {e}")
            return None
    
    def set(self, key: str, data: Any) -> None:
        """데이터를 캐시에 저장"""
        cache_file = self.get_cache_path(key)
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"캐시 저장 실패: {e}")
    
    def clear_expired(self, max_age: int = 3600) -> None:
        """만료된 캐시 정리"""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cache_time > timedelta(seconds=max_age):
                    cache_file.unlink()
            except Exception:
                # 손상된 캐시 파일 삭제
                cache_file.unlink()

def format_duration(seconds: float) -> str:
    """초를 시:분:초 형태로 변환"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def format_filesize(size_bytes: int) -> str:
    """바이트를 읽기 쉬운 형태로 변환"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """재시도 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"시도 {attempt + 1}/{max_retries} 실패. {delay}초 후 재시도... ({e})")
                        time.sleep(delay)
            logger.error(f"{func.__name__} 실패: 최대 재시도 횟수 초과.")
            raise last_exception
        return wrapper
    return decorator

# 전역 인스턴스
config_manager = ConfigManager()
cache_manager = CacheManager()
