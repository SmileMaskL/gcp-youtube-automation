from PIL import Image, ImageDraw, ImageFont
import requests
import os
from pathlib import Path
import random
import logging
from .config import Config

logger = logging.getLogger(__name__)

def create_thumbnail(text: str, background_path: str, output_path: str):
    """썸네일 이미지 생성"""
    try:
        # 1. 배경 이미지 로드
        img = Image.open(background_path)
        img = img.resize((Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT))
        
        # 2. 어두운 오버레이 추가
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 128))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        # 3. 폰트 설정 (고양이체)
        try:
            font = ImageFont.truetype(str(Config.FONT_PATH), 80)
        except:
            font = ImageFont.load_default()
            logger.warning("고양이체 폰트 로드 실패. 기본 폰트 사용")
        
        # 4. 텍스트 렌더링
        lines = textwrap.wrap(text, width=15)  # 15자 단위로 줄바꿈
        y_offset = (Config.SHORTS_HEIGHT - (len(lines) * 100)) // 2  # 중앙 정렬
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (Config.SHORTS_WIDTH - text_width) / 2
            draw.text((x, y_offset), line, font=font, fill="white", stroke_width=3, stroke_fill="black")
            y_offset += 100
        
        # 5. 서브 타이틀 추가
        draw.text((50, Config.SHORTS_HEIGHT - 150), "지금 바로 확인하세요!", 
                 font=ImageFont.truetype(str(Config.FONT_PATH), 40) if Config.FONT_PATH.exists() else ImageFont.load_default(), 
                 fill="yellow")
        
        # 6. 저장
        img.save(output_path)
        logger.info(f"썸네일 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"썸네일 생성 실패: {str(e)}")
        raise
