from PIL import Image, ImageDraw, ImageFont
import requests
import os
from pathlib import Path
import random
import logging

# 로거 설정 추가
logger = logging.getLogger(__name__)

def generate_thumbnail(topic: str) -> str:
    """썸네일 이미지 생성"""
    try:
        # 1. Pexels에서 이미지 다운로드
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            logger.warning("PEXELS_API_KEY가 없습니다. 기본 배경 사용")
            return create_default_thumbnail(topic)
            
        headers = {"Authorization": api_key}
        url = f"https://api.pexels.com/v1/search?query={topic}&per_page=1"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200 or not response.json().get('photos'):
            logger.warning("Pexels에서 이미지를 가져오지 못함. 기본 배경 사용")
            return create_default_thumbnail(topic)
            
        photo = response.json()['photos'][0]
        img_url = photo['src']['original']
        img_content = requests.get(img_url).content
            
        # 2. 임시 파일 저장
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        bg_path = temp_dir / f"{topic}_bg.jpg"
        
        with open(bg_path, "wb") as f:
            f.write(img_content)
            
        # 3. 썸네일 제작
        img = Image.open(bg_path)
        img = img.resize((1080, 1920))
        
        # 이미지 어둡게 처리
        overlay = Image.new('RGBA', img.size, (0,0,0,128))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        # 폰트 설정 (고양이체 사용)
        try:
            font_path = "fonts/Catfont.ttf"
            title_font = ImageFont.truetype(font_path, 80)
            subtitle_font = ImageFont.truetype(font_path, 50)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # 제목 그리기
        text = topic.upper()
        bbox = draw.textbbox((0, 0), text, font=title_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (1080 - text_width) / 2
        y = (1920 - text_height) / 2
        
        draw.text((x, y), text, font=title_font, fill="white", stroke_width=3, stroke_fill="black")
        
        # 서브타이틀
        draw.text((50, 1700), "클릭해서 확인하세요!", font=subtitle_font, fill="yellow")
        
        # 4. 썸네일 저장
        thumbnail_path = temp_dir / f"{topic}_thumbnail.jpg"
        img.save(thumbnail_path)
        
        # 배경 이미지 삭제
        bg_path.unlink()
        
        return str(thumbnail_path)
        
    except Exception as e:
        logger.error(f"썸네일 생성 실패: {str(e)}")
        return create_default_thumbnail(topic)

def create_default_thumbnail(topic: str) -> str:
    """기본 썸네일 생성"""
    try:
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        thumbnail_path = temp_dir / f"{topic}_default_thumbnail.jpg"
        
        img = Image.new('RGB', (1080, 1920), color=(70, 130, 180))
        draw = ImageDraw.Draw(img)
        
        try:
            font_path = "fonts/Catfont.ttf"
            font = ImageFont.truetype(font_path, 80)
        except:
            font = ImageFont.load_default()
            
        text = topic.upper()
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (1080 - (bbox[2] - bbox[0])) / 2
        y = (1920 - (bbox[3] - bbox[1])) / 2
        
        draw.text((x, y), text, font=font, fill="white")
        img.save(thumbnail_path)
        
        return str(thumbnail_path)
    except Exception as e:
        logger.error(f"기본 썸네일 생성 실패: {str(e)}")
        raise
