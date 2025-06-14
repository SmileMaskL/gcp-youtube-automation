"""
유틸리티 함수들 (완전 수정 버전 - 수익 최적화)
"""
"""
유틸리티 함수들 (완전 수정 버전 - 수익 최적화)
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
import random
from moviepy.editor import *
import openai
import google.generativeai as genai

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
    """텍스트를 음성으로 변환 (완전 수정 버전)"""
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
        # 백업: 무음 파일 생성
        temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp3")
        silent_audio = AudioClip(lambda t: 0, duration=len(text) * 0.1)
        silent_audio.write_audiofile(temp_path, logger=None)
        return temp_path


def generate_trending_content() -> Dict[str, Any]:
    """수익 최적화를 위한 트렌딩 콘텐츠 생성"""
    trending_topics = [
        "AI 기술 혁신", "암호화폐 투자", "부동산 투자", "주식 투자",
        "온라인 비즈니스", "디지털 마케팅", "유튜브 수익화", "블로그 수익화",
        "스타트업 창업", "사이드 프로젝트", "재테크", "경제 뉴스",
        "기술 트렌드", "미래 전망", "성공 스토리"
    ]

    topic = random.choice(trending_topics)

    # GPT-4o 또는 Gemini를 사용한 콘텐츠 생성
    try:
        content = generate_ai_content(topic)
        return {
            "topic": topic,
            "title": content["title"],
            "script": content["script"],
            "keywords": content["keywords"],
            "hashtags": content["hashtags"]
        }
    except Exception as e:
        logger.error(f"AI 콘텐츠 생성 실패: {e}")
        return get_fallback_content(topic)


def generate_ai_content(topic: str) -> Dict[str, Any]:
    """AI를 사용한 콘텐츠 생성 (GPT-4o 또는 Gemini)"""
    try:
        # 먼저 Gemini 시도 (무료)
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""
        다음 주제로 유튜브 쇼츠용 콘텐츠를 만들어주세요: {topic}

        요구사항:
        1. 제목: 클릭률이 높은 제목 (30자 이내)
        2. 대본: 60초 분량의 스크립트 (500자 이내)
        3. 키워드: SEO용 키워드 5개
        4. 해시태그: 트렌드 해시태그 10개

        JSON 형식으로 답변해주세요.
        """

        response = model.generate_content(prompt)
        content = json.loads(response.text)
        return content

    except Exception as e:
        logger.warning(f"Gemini 실패, GPT-4o 시도: {e}")
        try:
            # GPT-4o 시도
            openai.api_key = os.getenv("OPENAI_API_KEY")

            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "유튜브 쇼츠 콘텐츠 전문가입니다."},
                    {"role": "user", "content": f"'{topic}' 주제로 유튜브 쇼츠 콘텐츠를 JSON 형식으로 만들어주세요."}
                ],
                max_tokens=500
            )

            content = json.loads(response.choices[0].message.content)
            return content

        except Exception as e2:
            logger.error(f"GPT-4o도 실패: {e2}")
            raise


def get_fallback_content(topic: str) -> Dict[str, Any]:
    """AI 실패시 사용할 백업 콘텐츠"""
    return {
        "topic": topic,
        "title": f"{topic}에 대한 놀라운 사실!",
        "script": f"오늘은 {topic}에 대해 알아보겠습니다. 이 분야는 현재 매우 주목받고 있으며, 많은 기회가 있습니다. 여러분도 이 기회를 놓치지 마세요!",
        "keywords": [
            topic,
            "투자",
            "수익",
            "기회",
            "성공"],
        "hashtags": [
            "#투자",
            "#수익",
            "#성공",
            "#기회",
            "#돈",
            "#재테크",
            "#부업",
            "#사업",
            "#창업",
            "#미래"]}


def download_video_from_pexels(query: str = None) -> str:
    """Pexels에서 무료 비디오 다운로드"""
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return create_simple_video()

        # 수익성 높은 키워드 사용
        trending_queries = [
            "success",
            "money",
            "business",
            "technology",
            "future",
            "growth",
            "investment",
            "digital"]
        search_query = query or random.choice(trending_queries)

        headers = {"Authorization": api_key}
        url = f"https://api.pexels.com/videos/search?query={search_query}&per_page=10&orientation=portrait"

        response = requests.get(url, headers=headers)
        data = response.json()

        if data.get("videos"):
            video = random.choice(data["videos"])
            video_url = video["video_files"][0]["link"]

            # 비디오 다운로드
            video_response = requests.get(video_url)
            temp_path = os.path.join(
                tempfile.gettempdir(), f"{
                    uuid.uuid4()}.mp4")

            with open(temp_path, "wb") as f:
                f.write(video_response.content)

            return temp_path
        else:
            return create_simple_video()

    except Exception as e:
        logger.error(f"Pexels 비디오 다운로드 실패: {e}")
        return create_simple_video()


def create_simple_video() -> str:
    """간단한 비디오 생성 (백업용)"""
    try:
        # 컬러풀한 배경 비디오 생성
        colors = [
            "#FF6B6B",
            "#4ECDC4",
            "#45B7D1",
            "#96CEB4",
            "#FFEAA7",
            "#DDA0DD"]
        color = random.choice(colors)

        clip = ColorClip(size=(1080, 1920), color=color, duration=60)
        temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp4")
        clip.write_videofile(temp_path, fps=30, logger=None)

        return temp_path
    except Exception as e:
        logger.error(f"간단한 비디오 생성 실패: {e}")
        raise


def add_text_to_clip(video_path: str, text: str, output_path: str) -> str:
    """비디오에 텍스트 추가 (완전 수정)"""
    try:
        video = VideoFileClip(video_path)

        # 텍스트 스타일 (수익 최적화)
        txt_clip = TextClip(
            text,
            fontsize=60,
            color='white',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=3,
            method='caption',
            size=(video.w * 0.8, None)
        ).set_position('center').set_duration(video.duration)

        # 텍스트를 비디오에 합성
        final_video = CompositeVideoClip([video, txt_clip])
        final_video.write_videofile(output_path, fps=30, logger=None)

        # 메모리 정리
        video.close()
        txt_clip.close()
        final_video.close()

        return output_path

    except Exception as e:
        logger.error(f"텍스트 추가 실패: {e}")
        # 원본 비디오 반환
        return video_path


def optimize_for_revenue() -> Dict[str, Any]:
    """수익 최적화 설정"""
    return {
        "upload_schedule": "daily",  # 매일 업로드
        "best_times": ["09:00", "12:00", "18:00", "21:00"],  # 최적 업로드 시간
        "content_types": [
            "투자 팁", "부업 아이디어", "성공 스토리", "기술 트렌드",
            "경제 뉴스", "재테크", "창업 아이디어", "온라인 비즈니스"
        ],
        "monetization": {
            "enable_ads": True,
            "enable_memberships": True,
            "enable_super_chat": True,
            "enable_super_thanks": True
        },
        "seo_optimization": {
            "trending_keywords": [
                "돈 버는 방법", "투자", "부업", "재테크", "성공",
                "AI", "기술", "미래", "창업", "비즈니스"
            ]
        }
    }


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
        """기본 설정 반환 (수익 최적화)"""
        return {
            "video": {
                "resolution": "1080x1920",  # 쇼츠 최적화
                "fps": 30,
                "bitrate": "5000k",
                "format": "mp4",
                "duration": 60  # 쇼츠 최적 길이
            },
            "audio": {
                "bitrate": "128k",
                "sample_rate": 44100
            },
            "upload": {
                "auto_upload": True,
                "privacy": "public",  # 수익을 위해 공개
                "category": "22",  # People & Blogs
                "schedule": "daily",
                "times": ["09:00", "18:00"]
            },
            "revenue": optimize_for_revenue(),
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

    def __init__(
            self,
            base_url: str,
            api_key: str = None,
            rate_limit: RateLimiter = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.rate_limiter = rate_limit or RateLimiter()
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})

    def make_request(
            self,
            method: str,
            endpoint: str,
            **kwargs) -> requests.Response:
        """API 요청 실행"""
        # Rate limiting
        if not self.rate_limiter.can_make_call():
            wait_time = self.rate_limiter.wait_time()
            logger.info(
                f"Rate limit reached. Waiting {
                    wait_time:.2f} seconds...")
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
                        logger.warning(
                            f"시도 {
                                attempt + 1}/{max_retries} 실패. {delay}초 후 재시도... ({e})")
                        time.sleep(delay)
            logger.error(f"{func.__name__} 실패: 최대 재시도 횟수 초과.")
            raise last_exception
        return wrapper
    return decorator


# 전역 인스턴스
config_manager = ConfigManager()
cache_manager = CacheManager()
