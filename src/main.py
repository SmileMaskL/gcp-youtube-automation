# src/main.py (수정 및 보완된 전체 코드)

import functions_framework
import logging
import os
import json # JSON 응답을 위해 추가

from .config import Config
from .youtube_uploader import YouTubeUploader # 주석 해제 및 실제 사용
from .content_curator import ContentCurator # 콘텐츠 큐레이터 추가 (수익 창출 로직)
from .video_creator import VideoCreator # 영상 생성 로직 추가
from .tts_generator import TTSGenerator # TTS 생성 로직 추가
from .utils import load_config # config.py에서 load_config 함수 가져오기 (환경변수 로딩용)

# 로깅 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

_config = None

def get_config():
    global _config
    if _config is None:
        try:
            logger.info("Config 인스턴스 생성 시도...")
            # 환경 변수 로드 (GCP_PROJECT_ID, GCP_BUCKET_NAME 등)
            env_vars = {
                "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID"),
                "GCP_BUCKET_NAME": os.getenv("GCP_BUCKET_NAME"),
                "ELEVENLABS_VOICE_ID": os.getenv("ELEVENLABS_VOICE_ID") # Secret Manager에서 직접 가져오지 않는 경우를 대비
            }
            # Config 클래스에 필요한 모든 환경 변수 또는 Secret Manager 참조 전달
            _config = Config(env_vars=env_vars)
            logger.info("Config 인스턴스 생성 성공.")
        except Exception as e:
            logger.critical(f"Config 인스턴스 생성 중 치명적인 오류 발생: {e}", exc_info=True)
            raise
    return _config

@functions_framework.http
def youtube_automation_main(request):
    logger.info("함수 호출 시작: youtube_automation_main")
    
    try:
        # 요청 바디 파싱 (만약 특정 트리거 데이터가 있다면)
        request_json = request.get_json(silent=True)
        is_daily_run = request_json.get('daily_run', False) if request_json else False
        logger.info(f"일일 실행 여부: {is_daily_run}")

        config = get_config()

        # Secret Manager에서 API 키 가져오기 (매 호출마다 가져오도록 변경)
        youtube_client_id = config.get_youtube_client_id()
        youtube_client_secret = config.get_youtube_client_secret()
        youtube_refresh_token = config.get_youtube_refresh_token()
        elevenlabs_api_key = config.get_elevenlabs_api_key()
        openai_api_key = config.get_openai_api_key() # OpenAI API 키 추가
        newsapi_api_key = config.get_newsapi_api_key() # NewsAPI 키 추가
        pexels_api_key = config.get_pexels_api_key() # Pexels API 키 추가 (만약 사용한다면)

        logger.info("모든 Secret Manager 값 로드 완료.")

        # --- 핵심 로직 시작 (주석 해제 및 기능 추가) ---

        # 1. 콘텐츠 큐레이션 (yt-dlp, newsapi, Pexels API 등 활용)
        # NewsAPI 키가 있다면 ContentCurator 초기화
        # PexelsApi를 제거했으므로, Pexels 이미지를 가져오는 로직은 수정하거나 제거해야 합니다.
        # 여기서는 NewsAPI만 사용하는 예시를 들겠습니다.
        content_curator = ContentCurator(news_api_key=newsapi_api_key)
        
        # 실제 수익 창출을 위한 콘텐츠 아이디어 가져오기 (예시)
        # 뉴스 기사를 통해 Shorts 주제를 얻거나, 인기 키워드를 크롤링
        try:
            # 예를 들어, 'technology' 카테고리에서 최신 뉴스 헤드라인을 가져와 주제로 사용
            headlines = content_curator.get_top_headlines(query='technology', language='en', page_size=5)
            if headlines:
                topic = headlines[0]['title'] # 첫 번째 헤드라인을 주제로 사용
                logger.info(f"큐레이션된 주제: {topic}")
            else:
                topic = "오늘의 흥미로운 사실"
                logger.warning("뉴스 헤드라인을 가져오지 못하여 기본 주제를 사용합니다.")
        except Exception as e:
            topic = "오늘의 흥미로운 사실"
            logger.error(f"뉴스 큐레이션 중 오류 발생: {e}", exc_info=True)


        # 2. 텍스트 생성 (Gemini 또는 GPT-4o 사용)
        # 여기서는 Google Gemini를 사용한다고 가정합니다.
        # ai_manager = AIManager(api_key=openai_api_key, gemini_api_key=config.get_gemini_api_key()) # AI Manager 초기화
        # shorts_script = ai_manager.generate_script(topic) # 스크립트 생성
        
        # 간단한 예시로 Gemini API 호출 (실제 API 호출 로직은 gemini_utils.py에 구현 필요)
        # 여기서는 더미 텍스트 사용, 실제로는 gemini_utils.py의 함수 호출
        # from .gemini_utils import generate_text_with_gemini
        # shorts_script = generate_text_with_gemini(f"'{topic}'에 대한 YouTube Shorts 대본을 500자 이내로 작성해줘.")
        
        # 임시 스크립트 (실제 AI 모델 연동 후 교체)
        shorts_script = f"안녕하세요! 오늘은 '{topic}'에 대해 이야기해볼게요. 놀라운 사실들이 여러분을 기다립니다! 자세한 내용은 아래 설명란을 확인해주세요. 구독과 좋아요는 저에게 큰 힘이 됩니다!"
        logger.info(f"생성된 스크립트: {shorts_script[:100]}...")


        # 3. TTS (Text-to-Speech) 생성 (ElevenLabs 사용)
        tts_generator = TTSGenerator(elevenlabs_api_key=elevenlabs_api_key, voice_id=config.elevenlabs_voice_id)
        audio_file_path = "/tmp/generated_audio.mp3" # Cloud Function은 /tmp에만 쓸 수 있음
        tts_generator.generate_audio(shorts_script, audio_file_path)
        logger.info(f"오디오 파일 생성 완료: {audio_file_path}")

        # 4. 영상 생성 및 편집 (shorts_converter, video_creator 등 활용)
        # bg_downloader, video_editor, shorts_converter, thumbnail_generator 등 모듈이 필요
        # 여기서는 가장 간단한 형태로 가정 (실제 구현은 복잡함)
        video_output_path = "/tmp/final_short.mp4"
        # VideoCreator 등 실제 영상 생성 로직 호출
        # 예시: (실제로는 복잡한 영상 생성 로직이 들어갑니다)
        # from .video_creator import VideoCreator
        # video_creator = VideoCreator(
        #    background_video_path="/tmp/background.mp4", # 배경 영상 다운로드 필요
        #    audio_path=audio_file_path,
        #    output_path=video_output_path
        # )
        # video_creator.create_video()
        
        # 임시 영상 생성 (실제 영상 생성 로직 후 교체)
        # 실제 영상 파일이 필요하므로, 테스트용으로 임시 파일을 생성하는 로직이나,
        # 미리 준비된 더미 영상을 사용하는 로직이 필요합니다.
        # Cloud Function 환경에서는 FFMPEG 등 영상 처리 도구를 직접 설치하기 어렵습니다.
        # 이를 해결하려면 Docker 기반의 Cloud Run을 사용하거나, FFMPEG 레이어를 Cloud Function에 추가해야 합니다.
        # 현재는 Cloud Function 환경이므로, 일단 임시로 아무 파일이나 생성합니다.
        # TODO: 실제 영상 생성 로직 구현 (가장 복잡한 부분)
        with open(video_output_path, 'wb') as f:
            f.write(b'\x00\x00\x00\x00') # 아주 작은 더미 파일 생성 (에러 방지용)
        logger.warning(f"임시 더미 영상 생성: {video_output_path}. 실제 영상 생성 로직 구현 필요!")
        
        # 5. YouTube 업로드
        uploader = YouTubeUploader(
            client_id=youtube_client_id,
            client_secret=youtube_client_secret,
            refresh_token=youtube_refresh_token,
            project_id=config.gcp_project_id,
            bucket_name=config.gcp_bucket_name # 버킷 이름을 Config에서 가져옴
        )
        
        video_title = f"데일리 쇼츠: {topic[:90]}" # 제목은 최대 100자
        video_description = f"오늘의 흥미로운 Shorts 영상입니다! {shorts_script}"
        tags = ["쇼츠", "자동화", "AI", "수익창출", topic.replace(" ", "_")] # 관련 태그 추가
        
        uploaded_video_id = uploader.upload_video(
            file_path=video_output_path,
            title=video_title,
            description=video_description,
            tags=tags,
            privacy_status='public' # 'public', 'private', 'unlisted' 중 선택
        )
        
        logger.info(f"YouTube 영상 업로드 성공! 영상 ID: {uploaded_video_id}")
        
        # 6. (선택 사항) 댓글 게시
        # CommentPoster 기능이 필요하다면 활성화 및 구현
        # commenter = CommentPoster(...)
        # commenter.post_comment(uploaded_video_id, "첫 댓글입니다!")

        # --- 핵심 로직 종료 ---

        response_message = f"YouTube Shorts 자동화 함수가 성공적으로 실행되었습니다. 업로드된 영상 ID: {uploaded_video_id}"
        logger.info(response_message)
        return response_message, 200

    except Exception as e:
        logger.error(f"함수 실행 중 오류 발생: {e}", exc_info=True)
        # 오류 발생 시 디버깅을 위해 더 자세한 정보 반환
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()}), 500
