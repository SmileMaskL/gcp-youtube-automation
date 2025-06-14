from pathlib import Path

class Config:
    """설정 클래스"""
    
    # 프로젝트 경로
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # 디렉토리 설정
    TEMP_DIR = PROJECT_ROOT / "temp"
    OUTPUT_DIR = PROJECT_ROOT / "output"
    CREDENTIALS_DIR = PROJECT_ROOT / "credentials"
    
    # 영상 설정 (유튜브 쇼츠 최적화)
    SHORTS_WIDTH = 1080   # 세로형 영상 너비
    SHORTS_HEIGHT = 1920  # 세로형 영상 높이
    SHORTS_ASPECT_RATIO = SHORTS_HEIGHT / SHORTS_WIDTH  # 16:9 세로형
    
    # 영상 품질 설정
    VIDEO_QUALITY = "hd"
    VIDEO_FPS = 24
    AUDIO_QUALITY = "128k"
    
    # API 설정
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30
    
    # 콘텐츠 설정
    MAX_TITLE_LENGTH = 100  # 유튜브 제목 최대 길이
    MAX_DESCRIPTION_LENGTH = 5000  # 유튜브 설명 최대 길이
    MAX_SCRIPT_LENGTH = 1000  # 스크립트 최대 길이
    
    # 일일 업로드 제한 (무료 한도 고려)
    DAILY_UPLOAD_LIMIT = 5
    
    # 유튜브 카테고리 ID
    YOUTUBE_CATEGORIES = {
        "교육": 27,
        "엔터테인먼트": 24,
        "라이프스타일": 26,
        "뉴스": 25,
        "기술": 28
    }
    
    # 기본 카테고리
    DEFAULT_CATEGORY = 26  # 라이프스타일
    
    # 지원하는 언어
    SUPPORTED_LANGUAGES = ["ko", "en", "ja", "zh"]
    DEFAULT_LANGUAGE = "ko"
    
    # 해시태그 설정
    MAX_HASHTAGS = 30
    TRENDING_HASHTAGS = [
        "#쇼츠", "#shorts", "#꿀팁", "#라이프해킹", "#자기계발",
        "#성공", "#부자", "#투자", "#부업", "#돈버는방법",
        "#건강", "#운동", "#다이어트", "#요리", "#여행",
        "#공부", "#취업", "#직장인", "#학생", "#주부"
    ]
