import os
import uuid
import random
import requests
import moviepy
from pathlib import Path
from moviepy.editor import *
import logging
from dotenv import load_dotenv
from gtts import gTTS
import google.generativeai as genai
from moviepy.config import change_settings
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess
import textwrap
from pexels_api import API  # Pexels 공식 API 클라이언트

# ✅ 필수 시스템 설정
change_settings({
    "FFMPEG_BINARY": "/usr/bin/ffmpeg",
    "IMAGEMAGICK_BINARY": "/usr/bin/convert"
})

# ✅ 호환성 패치 (Pillow 최신 버전 대응)
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

# --- 로거 설정 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- 환경 변수 및 설정 클래스 ---
load_dotenv()

class Config:
    TEMP_DIR = Path("temp")
    OUTPUT_DIR = Path("output")
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"
    
    # API 키
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

    @classmethod
    def initialize(cls):
        """필요한 디렉토리 생성 및 설정 확인"""
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        if not all([cls.GEMINI_API_KEY, cls.ELEVENLABS_API_KEY, cls.PEXELS_API_KEY]):
            raise ValueError("필수 API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        
        genai.configure(api_key=cls.GEMINI_API_KEY)

# --- 핵심 기능 함수 ---

def generate_content() -> dict:
    """Gemini로 유튜브 쇼츠 콘텐츠 생성"""
    logger.info("🤖 Gemini로 콘텐츠 생성을 시작합니다...")
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = """유튜브 쇼츠용 콘텐츠를 다음 형식으로 생성해주세요:
        {
          "title": "영감을 주는 제목 (15자 이내)",
          "script": "간결하고 강력한 대본 (3문장 이내)",
          "pexel_query": "영상 검색용 영어 키워드"
        }"""
        response = model.generate_content(prompt)
        content = eval(response.text.strip())
        logger.info(f"✅ 콘텐츠 생성 완료: {content['title']}")
        return content
    except Exception as e:
        logger.error(f"❌ 콘텐츠 생성 실패: {e}")
        return {
            "title": "성공의 비밀",
            "script": "성공의 첫 번째 비밀은 꾸준함입니다. 매일 조금씩이라도 진행하세요.",
            "pexel_query": "success motivation"
        }

def generate_tts(script: str) -> Path:
    """음성 생성 (ElevenLabs -> gTTS 폴백)"""
    logger.info("🎤 음성 생성을 시작합니다...")
    audio_path = Config.TEMP_DIR / f"{uuid.uuid4()}.mp3"
    try:
        # ElevenLabs 시도
        headers = {
            "xi-api-key": Config.ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "text": script,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{Config.ELEVENLABS_VOICE_ID}",
            headers=headers,
            json=data
        )
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
        except Exception as e:
            logger.error(f"❌ gTTS도 실패: {e}")
            raise

def get_background_video(query: str, duration: int) -> Path:
    """배경 영상 가져오기 (Pexels -> 단색 배경 폴백)"""
    logger.info(f"🎥 배경 영상 검색: '{query}'")
    video_path = Config.TEMP_DIR / f"{uuid.uuid4()}.mp4"
    
    try:
        # Pexels API 사용
        api = API(Config.PEXELS_API_KEY)
        api.search_videos(query, page=1, results_per_page=5)
        
        if not api.videos:
            raise ValueError("검색 결과 없음")
        
        video_url = random.choice(api.videos)['video_files'][0]['link']
        
        with requests.get(video_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(video_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info("✅ Pexels 영상 다운로드 완료")
        return video_path
    except Exception as e:
        logger.warning(f"⚠️ Pexels 실패 ({e}), 단색 배경으로 대체합니다.")
        try:
            # FFmpeg로 단색 배경 동영상 생성
            color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'color=c={color[0]:02x}{color[1]:02x}{color[2]:02x}:r=24:d={duration}:s={Config.SHORTS_WIDTH}x{Config.SHORTS_HEIGHT}',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-y', str(video_path)
            ]
            subprocess.run(cmd, check=True)
            return video_path
        except Exception as e:
            logger.error(f"❌ 단색 배경 생성 실패: {e}")
            raise

def create_final_video(content: dict, audio_path: Path, bg_video_path: Path) -> Path:
    """최종 영상 생성"""
    logger.info("🎬 최종 비디오 제작을 시작합니다...")
    
    # 리소스 관리를 위해 별도 함수로 분리
    def generate_text_clip(script: str, duration: float) -> ImageClip:
        """메모리 효율적인 텍스트 클립 생성"""
        text_img = Image.new('RGBA', (Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)
        try:
            font = ImageFont.truetype(Config.FONT_PATH, 60)
        except:
            font = ImageFont.load_default()
        
        lines = textwrap.wrap(script, width=20)
        y_text = (Config.SHORTS_HEIGHT - len(lines)*60) // 2
        
        for line in lines:
            w, h = draw.textsize(line, font=font)
            draw.text(
                ((Config.SHORTS_WIDTH-w)/2, y_text),
                line, font=font, fill="white",
                stroke_width=2, stroke_fill="black"
            )
            y_text += 60
        
        text_path = Config.TEMP_DIR / f"text_{uuid.uuid4()}.png"
        text_img.save(str(text_path))
        return ImageClip(str(text_path)).set_duration(duration)
    
    try:
        # 오디오 클립 준비
        audio_clip = AudioFileClip(str(audio_path))
        duration = audio_clip.duration
        
        # 배경 영상 클립 준비
        bg_clip = VideoFileClip(str(bg_video_path))
        bg_clip = bg_clip.subclip(0, duration).resize(height=Config.SHORTS_HEIGHT)
        
        # 텍스트 클립 생성 (최신 Pillow 호환 방식)
        text_img = Image.new('RGBA', (Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)
        try:
            font = ImageFont.truetype(Config.FONT_PATH, 60)
        except:
            font = ImageFont.load_default()
        
        lines = textwrap.wrap(content["script"], width=20)
        y_text = (Config.SHORTS_HEIGHT - len(lines)*60) // 2
        
        for line in lines:
            w, h = draw.textsize(line, font=font)
            draw.text(
                ((Config.SHORTS_WIDTH-w)/2, y_text),
                line, font=font, fill="white",
                stroke_width=2, stroke_fill="black"
            )
            y_text += 60
        
        text_path = Config.TEMP_DIR / f"text_{uuid.uuid4()}.png"
        text_img.save(str(text_path))
        
        text_clip = ImageClip(str(text_path)).set_duration(duration)
        
        # 최종 영상 합성
        final_clip = CompositeVideoClip([bg_clip, text_clip])
        final_clip = final_clip.set_audio(audio_clip)
        
        output_path = Config.OUTPUT_DIR / f"shorts_{uuid.uuid4()}.mp4"
        final_clip.write_videofile(
            str(output_path),
            fps=24,
            codec='libx264',
            audio_codec='aac',
            threads=2,
            preset='ultrafast',
            ffmpeg_params=['-crf', '28']
        )
        
        logger.info(f"✅ 최종 영상 생성 완료: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"❌ 비디오 제작 실패: {e}")
        raise
    finally:
        if 'audio_clip' in locals(): audio_clip.close()
        if 'bg_clip' in locals(): bg_clip.close()
        if 'text_clip' in locals(): text_clip.close()

def cleanup():
    """임시 파일 정리"""
    logger.info("🗑️ 임시 파일 정리 중...")
    for f in Config.TEMP_DIR.glob("*"):
        try:
            f.unlink()
        except Exception as e:
            logger.warning(f"파일 삭제 실패: {f} - {e}")

def main():
    """메인 실행 함수"""
    try:
        Config.initialize()
        content = generate_content()
        audio_path = generate_tts(content["script"])
        bg_path = get_background_video(content["pexel_query"], 60)
        final_path = create_final_video(content, audio_path, bg_path)
        logger.info(f"🎉 성공! 생성된 영상: {final_path}")
        return final_path
    except Exception as e:
        logger.error(f"💥 치명적 오류: {e}", exc_info=True)
        raise
    finally:
        cleanup()

if __name__ == "__main__":
    main()
