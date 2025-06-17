from PIL import Image, ImageDraw, ImageFont, ImageOps
import textwrap
from pathlib import Path
import logging
from .config import Config

logger = logging.getLogger(__name__)

def create_thumbnail(text: str, background_path: str, output_path: str):
    """썸네일 생성 (최종확인 버전)"""
    try:
        # 1. 배경 이미지 로드 및 리사이즈
        img = Image.open(background_path)
        img = ImageOps.fit(img, (Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT))
        
        # 2. 어두운 오버레이 추가
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 128))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        # 3. 폰트 설정
        try:
            title_font = ImageFont.truetype(str(Config.FONT_PATH), 80)
            subtitle_font = ImageFont.truetype(str(Config.FONT_PATH), 40)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            logger.warning("폰트 로드 실패. 기본 폰트 사용")
        
        # 4. 텍스트 렌더링 (자동 줄바꿈)
        lines = textwrap.wrap(text, width=15)
        y_pos = (Config.SHORTS_HEIGHT - len(lines)*100) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            text_width = bbox[2] - bbox[0]
            x_pos = (Config.SHORTS_WIDTH - text_width) // 2
            draw.text((x_pos, y_pos), line, font=title_font, fill="white", stroke_width=3, stroke_fill="black")
            y_pos += 100
        
        # 5. 서브 타이틀 추가
        draw.text((50, Config.SHORTS_HEIGHT-150), "지금 바로 확인하세요!", 
                font=subtitle_font, fill="yellow")
        
        # 6. 저장
        img.save(output_path)
        logger.info(f"썸네일 저장: {output_path}")
        
    except Exception as e:
        logger.error(f"썸네일 생성 실패: {e}")
        raise
