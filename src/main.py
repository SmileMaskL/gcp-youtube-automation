import os
import uuid
import random
import requests
from pathlib import Path
from moviepy.editor import *
import logging
from dotenv import load_dotenv
from gtts import gTTS
import google.generativeai as genai
from pexels_api import API
import textwrap
from PIL import Image, ImageDraw, ImageFont
resized_img = img.resize((width, height), Image.LANCZOS)

# --- 로거 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 환경 변수 및 설정 클래스 ---
load_dotenv()

class Config:
    TEMP_DIR = Path("temp")
    OUTPUT_DIR = Path("output")
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    # Noto CJK 폰트 경로 (GitHub Actions에 설치된 폰트)
    FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"
    
    # API 키
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM") # 기본값 설정
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

    @classmethod
    def initialize(cls):
        """필요한 디렉토리를 생성하고 모든 API 키가 있는지 확인합니다."""
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        if not all([cls.GEMINI_API_KEY, cls.ELEVENLABS_API_KEY, cls.PEXELS_API_KEY]):
            raise ValueError("하나 이상의 API 키가 설정되지 않았습니다. GitHub Secrets를 확인하세요.")
        
        genai.configure(api_key=cls.GEMINI_API_KEY)

# --- 핵심 기능 함수 ---

def generate_content() -> dict:
    """Gemini를 사용하여 유튜브 쇼츠용 콘텐츠 생성"""
    logger.info("🤖 Gemini로 콘텐츠 생성을 시작합니다...")
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        prompt = """
        유튜브 쇼츠 영상 대본을 한국어로 생성해 줘. 반드시 아래 JSON 형식을 따라야 해.
        주제는 '성공, 부, 동기부여' 중 하나로 무작위로 정해줘.
        
        {
          "title": "영상 제목 (강력하고 짧게)",
          "script": "영상에 사용할 전체 대본 (3~4 문장, 15초 분량)",
          "pexel_query": "배경 영상 검색을 위한 영어 키워드 (2-3 단어)"
        }
        """
        response = model.generate_content(prompt)
        # 응답 텍스트에서 JSON 부분만 추출
        json_response = response.text.strip().split('```json\n')[1].split('\n```')[0]
        content = eval(json_response) # 문자열을 딕셔너리로 변환
        logger.info(f"✅ 콘텐츠 생성 완료: {content['title']}")
        return content
    except Exception as e:
        logger.error(f"❌ Gemini 콘텐츠 생성 실패: {e}", exc_info=True)
        raise

def generate_tts(script: str) -> Path:
    """ElevenLabs 또는 gTTS를 사용하여 오디오 파일 생성"""
    logger.info("🎤 음성 생성을 시작합니다...")
    audio_path = Config.TEMP_DIR / f"{uuid.uuid4()}.mp3"
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{Config.ELEVENLABS_VOICE_ID}"
        headers = {"xi-api-key": Config.ELEVENLABS_API_KEY, "Content-Type": "application/json"}
        data = {"text": script, "model_id": "eleven_multilingual_v2"}
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        with open(audio_path, "wb") as f:
            f.write(response.content)
        logger.info("✅ ElevenLabs 음성 생성 완료")
        return audio_path
    except Exception as e:
        logger.warning(f"⚠️ ElevenLabs 실패 ({e}), gTTS로 대체합니다.")
        try:
            tts = gTTS(text=script, lang='ko')
            tts.save(str(audio_path))
            logger.info("✅ gTTS 음성 생성 완료")
            return audio_path
        except Exception as gtts_e:
            logger.error(f"❌ gTTS마저 실패: {gtts_e}", exc_info=True)
            raise

def get_background_video(query: str, duration: int) -> Path:
    """Pexels API를 사용하여 배경 영상 다운로드, 실패 시 단색 배경 생성"""
    logger.info(f"🎥 배경 영상 검색: '{query}'")
    video_path = Config.TEMP_DIR / f"{uuid.uuid4()}.mp4"
    try:
        api = API(Config.PEXELS_API_KEY)
        api.search(query, page=1, results_per_page=5)
        if not api.videos:
            raise ValueError("Pexels에서 검색 결과 없음")
        
        pexels_video_url = random.choice(api.videos).video_files[0].link
        
        with requests.get(pexels_video_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(video_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info("✅ Pexels 영상 다운로드 완료")
        return video_path
    except Exception as e:
        logger.warning(f"⚠️ Pexels 영상 다운로드 실패 ({e}), 단색 배경으로 대체합니다.")
        color_clip = ColorClip(
            size=(Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT), 
            color=(random.randint(0,100), random.randint(0,100), random.randint(0,100)),
            duration=duration
        )
        color_clip.write_videofile(str(video_path), fps=24, logger=None)
        return video_path

def create_final_video(content: dict, audio_path: str, bg_video_path: str) -> Path:
    """모든 요소를 합쳐 최종 쇼츠 비디오를 제작"""
    logger.info("🎬 최종 비디오 제작을 시작합니다...")
    try:
        audio_clip = AudioFileClip(str(audio_path))
        video_duration = audio_clip.duration + 0.5  # 0.5초 여유

        bg_clip = VideoFileClip(str(bg_video_path)).set_duration(video_duration).resize(height=Config.SHORTS_HEIGHT)
        bg_clip = bg_clip.set_position("center").crop(width=Config.SHORTS_WIDTH, height=Config.SHORTS_HEIGHT)
        
        # 자막(TextClip) 생성
        wrapped_text = "\n".join(textwrap.wrap(content["script"], width=20))
        subtitle_clip = TextClip(
            wrapped_text,
            fontsize=70,
            color='white',
            font=Config.FONT_PATH,
            stroke_color='black',
            stroke_width=2,
            method='pillow',
            size=(Config.SHORTS_WIDTH*0.8, None)
        ).set_position(('center', 'center')).set_duration(video_duration)

        final_clip = CompositeVideoClip([bg_clip, subtitle_clip]).set_audio(audio_clip)
        
        output_path = Config.OUTPUT_DIR / f"shorts_{uuid.uuid4()}.mp4"
        final_clip.write_videofile(
            str(output_path), 
            fps=24, 
            codec='libx264', 
            audio_codec='aac',
            threads=2, # GitHub Actions 환경에 맞게 스레드 수 조절
            logger=None
        )
        logger.info(f"✅ 최종 비디오 제작 완료: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"❌ 비디오 제작 중 심각한 오류 발생: {e}", exc_info=True)
        raise

def cleanup():
    """임시 파일 정리"""
    logger.info("🗑️ 임시 파일을 정리합니다...")
    for f in Config.TEMP_DIR.glob("*"):
        try:
            f.unlink()
        except OSError as e:
            logger.warning(f"임시 파일 삭제 실패: {e}")

def main():
    """메인 실행 함수"""
    try:
        Config.initialize()
        content = generate_content()
        audio_path = generate_tts(content["script"])
        # 오디오 길이를 기반으로 배경 영상 길이 결정
        audio_duration = AudioFileClip(str(audio_path)).duration
        bg_video_path = get_background_video(content["pexel_query"], int(audio_duration) + 1)
        create_final_video(content, audio_path, bg_video_path)
    except Exception as e:
        logger.error(f"😭 프로세스 실행 중 최종 오류 발생: {e}")
        # 실패하더라도 프로그램이 0이 아닌 코드로 종료되도록 raise
        raise
    finally:
        cleanup()

if __name__ == "__main__":
    main()
