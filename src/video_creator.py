import os
import subprocess
from pathlib import Path
from config import Config
import uuid
from PIL import Image, ImageDraw, ImageFont
import textwrap
import logging

logger = logging.getLogger(__name__)

def create_text_image(title, script, output_path):
    """텍스트를 이미지로 렌더링"""
    # 흰색 배경 이미지 생성
    img = Image.new('RGB', (Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT), color='black')
    d = ImageDraw.Draw(img)
    
    # 폰트 로드 (상대 경로)
    font_path = Config.FONT_PATH
    title_font = ImageFont.truetype(font_path, 80)
    script_font = ImageFont.truetype(font_path, 60)
    
    # 제목 그리기
    title_lines = textwrap.wrap(title, width=20)
    title_y = (Config.SHORTS_HEIGHT // 4) - (len(title_lines) * 90 // 2)
    for line in title_lines:
        w, h = d.textsize(line, font=title_font)
        d.text(((Config.SHORTS_WIDTH - w) / 2, title_y), line, font=title_font, fill="white")
        title_y += 90
    
    # 대본 그리기
    script_lines = textwrap.wrap(script, width=30)
    script_y = (Config.SHORTS_HEIGHT // 2) - (len(script_lines) * 70 // 2)
    for line in script_lines:
        w, h = d.textsize(line, font=script_font)
        d.text(((Config.SHORTS_WIDTH - w) / 2, script_y), line, font=script_font, fill="white")
        script_y += 70
    
    img.save(output_path)

def create_video(content, audio_path, bg_path):
    """영상 생성 (Pillow 이미지 + FFmpeg 합성)"""
    output_path = Config.OUTPUT_DIR / f"shorts_{uuid.uuid4()}.mp4"
    temp_image = Config.TEMP_DIR / f"text_{uuid.uuid4()}.png"
    
    try:
        # 텍스트 이미지 생성
        create_text_image(content['title'], content['script'], temp_image)
        
        # FFmpeg로 합성: 배경 비디오 + 텍스트 이미지 + 오디오
        # 텍스트 이미지를 알파 채널이 있는 RGBA로 변환하여 오버레이
        cmd = [
            'ffmpeg',
            '-i', str(bg_path),
            '-i', str(temp_image),
            '-i', str(audio_path),
            '-filter_complex',
            '[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[bg];'
            '[bg][1:v]overlay=0:0[vid]',
            '-map', '[vid]',
            '-map', '2:a',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-shortest',
            '-y', str(output_path)
        ]
        subprocess.run(cmd, check=True)
        return output_path
    except Exception as e:
        logger.error(f"영상 생성 실패: {e}")
        raise
    finally:
        # 임시 이미지 삭제
        if temp_image.exists():
            os.remove(temp_image)
