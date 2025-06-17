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
        
        # 폰트 로드 (시스템 폰트 대신 프로젝트 폰트 사용)
        font = ImageFont.truetype(str(Config.FONT_PATH), 60)
        
        # 제목 렌더링
        draw.text((50, 200), title, font=font, fill="white")
        
        # 대본 렌더링 (자동 줄바꿈)
        y_offset = 400
        for line in textwrap.wrap(script, width=40):
            draw.text((50, y_offset), line, font=font, fill="white")
            y_offset += 70
            
        img.save(output_path)
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
        subprocess.run([
            "ffmpeg",
            "-i", str(bg_path),  # 배경 영상
            "-i", str(text_image),  # 텍스트 이미지
            "-i", str(audio_path),  # 오디오 파일
            "-filter_complex",
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[bg];"
            "[bg][1:v]overlay=0:0[vid]",  # 텍스트 오버레이
            "-map", "[vid]",
            "-map", "2:a",  # 오디오 매핑
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",  # 가장 짧은 입력에 맞춤
            "-y", str(output_path)  # 덮어쓰기 허용
        ], check=True)
        
        logger.info(f"영상 생성 완료: {output_path}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"영상 생성 실패 (FFmpeg 오류): {e}")
        raise
    except Exception as e:
        logger.error(f"영상 생성 실패: {e}")
        raise
