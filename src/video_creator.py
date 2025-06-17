import subprocess
import uuid
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap
from config import Config
import logging

logger = logging.getLogger(__name__)

def render_text_image(title, script, output_path):
    """텍스트 이미지 렌더링"""
    try:
        img = Image.new("RGB", (Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT), "black")
        draw = ImageDraw.Draw(img)
        
        # 폰트 로드
        try:
            font = ImageFont.truetype(str(Config.FONT_PATH), 60)
        except:
            font = ImageFont.load_default()
            logger.warning("기본 폰트 사용 중 - Catfont.ttf를 fonts 폴더에 추가하세요")
        
        # 제목 렌더링
        draw.text((50, 200), title, font=font, fill="white")
        
        # 대본 렌더링 (자동 줄바꿈)
        y_offset = 400
        for line in textwrap.wrap(script, width=40):
            draw.text((50, y_offset), line, font=font, fill="white")
            y_offset += 70
            
        img.save(output_path)
        logger.info(f"텍스트 이미지 생성 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"텍스트 이미지 생성 실패: {e}")
        raise

def create_video(content, audio_path, bg_path):
    """최종 영상 생성"""
    output_path = Config.OUTPUT_DIR / f"shorts_{uuid.uuid4()}.mp4"
    text_image = Config.TEMP_DIR / f"text_{uuid.uuid4()}.png"
    
    try:
        # 1. 텍스트 이미지 생성
        render_text_image(content["title"], content["script"], text_image)
        
        # 2. FFmpeg로 영상 합성
        cmd = [
            "ffmpeg",
            "-i", str(bg_path),
            "-i", str(text_image),
            "-i", str(audio_path),
            "-filter_complex",
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[bg];"
            "[bg][1:v]overlay=0:0[vid]",
            "-map", "[vid]",
            "-map", "2:a",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            "-y", str(output_path)
        ]
        
        logger.info(f"실행 명령어: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
        logger.info(f"영상 생성 완료: {output_path}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"영상 생성 실패 (FFmpeg 오류): {e}")
        raise
    except Exception as e:
        logger.error(f"영상 생성 실패: {e}")
        raise
