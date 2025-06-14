import os
import sys
import logging
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import Config
from src.utils import (
    generate_viral_content_gemini,
    generate_viral_content_gpt4o,
    generate_tts_with_elevenlabs,
    download_video_from_pexels,
    create_shorts_video,
    estimate_audio_duration,
    cleanup_temp_files
)
from src.youtube_uploader import YouTubeUploader

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_environment():
    """환경변수를 로드합니다."""
    env_file = project_root / '.env'
    if env_file.exists():
        logger.info(f".env 파일을 로드합니다: {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    else:
        logger.warning(".env 파일을 찾을 수 없습니다.")

def check_required_apis():
    """필수 API 키들이 설정되어 있는지 확인합니다."""
    required_apis = {
        'GEMINI_API_KEY': '구글 Gemini API',
        'ELEVENLABS_API_KEY': 'ElevenLabs API',
        'PEXELS_API_KEY': 'Pexels API (선택사항)'
    }
    
    missing_apis = []
    for key, name in required_apis.items():
        if not os.getenv(key):
            if key != 'PEXELS_API_KEY':  # Pexels는 선택사항
                missing_apis.append(f"{name} ({key})")
    
    if missing_apis:
        logger.error(f"다음 API 키들이 설정되지 않았습니다: {', '.join(missing_apis)}")
        logger.error("프로젝트 루트의 .env 파일에 API 키를 설정해주세요.")
        return False
    
    logger.info("모든 필수 API 키가 설정되었습니다.")
    return True

def main():
    """메인 실행 함수"""
    try:
        # 환경 설정
        load_environment()
        
        logger.info("=" * 50)
        logger.info("💰💰 유튜브 수익형 자동화 시스템 V4 (완결판) 시작 💰💰")
        logger.info("=" * 50)
        
        # 디렉토리 생성
        Config.TEMP_DIR.mkdir(exist_ok=True)
        Config.OUTPUT_DIR.mkdir(exist_ok=True)
        
        # API 키 확인
        if not check_required_apis():
            return
        
        # 오늘의 주제 설정
        topics = [
            "부자가 되는 사소한 습관",
            "성공하는 사람들의 아침 루틴",
            "돈 버는 부업 아이디어",
            "투자 초보자를 위한 꿀팁",
            "시간 관리의 비밀",
            "자기계발 필수 습관",
            "효율적인 공부법",
            "건강한 라이프스타일",
            "인간관계 개선 방법",
            "스트레스 해소법"
        ]
        
        import random
        topic = random.choice(topics)
        logger.info(f"🔥 오늘의 주제: {topic}")
        
        # 1단계: AI 콘텐츠 생성
        logger.info("1단계: AI 콘텐츠 생성 중...")
        try:
            content = generate_viral_content_gemini(topic)
        except Exception as e:
            logger.warning(f"Gemini 실패, GPT-4o로 시도: {e}")
            content = generate_viral_content_gpt4o(topic)
        
        logger.info(f"제목: {content['title']}")
        logger.info(f"스크립트 길이: {len(content['script'])}자")
        
        # 2단계: 음성 생성
        logger.info("2단계: 음성 생성 중...")
        audio_path = generate_tts_with_elevenlabs(content['script'])
        
        # 3단계: 배경 영상 준비
        logger.info("3단계: 배경 영상 준비 중...")
        estimated_duration = estimate_audio_duration(content['script'])
        video_path = download_video_from_pexels(topic, duration=estimated_duration)
        
        # 4단계: 최종 영상 생성
        logger.info("4단계: 최종 영상 생성 중...")
        final_video_path = create_shorts_video(video_path, audio_path, content['title'])
        
        # 5단계: 유튜브 업로드 (선택사항)
        logger.info("5단계: 유튜브 업로드 확인 중...")
        youtube_credentials = os.getenv("YOUTUBE_CREDENTIALS_PATH")
        if youtube_credentials and Path(youtube_credentials).exists():
            try:
                uploader = YouTubeUploader()
                video_url = uploader.upload_video(
                    video_path=final_video_path,
                    title=content['title'],
                    description=f"{content['script']}\n\n{' '.join(content['hashtags'])}",
                    tags=content['hashtags']
                )
                logger.info(f"✅ 유튜브 업로드 완료: {video_url}")
            except Exception as e:
                logger.warning(f"유튜브 업로드 실패: {e}")
        else:
            logger.info("유튜브 인증 정보가 없어 업로드를 건너뜁니다.")
        
        # 완료 메시지
        logger.info("=" * 50)
        logger.info("🎉 영상 생성이 완료되었습니다!")
        logger.info(f"📁 최종 영상: {final_video_path}")
        logger.info(f"📝 제목: {content['title']}")
        logger.info(f"🏷️ 해시태그: {' '.join(content['hashtags'])}")
        logger.info("=" * 50)
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 임시 파일 정리
        cleanup_temp_files()

if __name__ == "__main__":
    main()
