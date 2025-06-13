from PIL import Image, ImageDraw, ImageFont
import requests
from pexels_api import API
import os

def generate_thumbnail(topic: str) -> str:
    """썸네일 이미지 생성"""
    try:
        # 1. Pexels에서 무료 이미지 다운로드
        pexels = API(os.getenv("PEXELS_API_KEY"))
        search = pexels.search_photo(topic, page=1, results_per_page=1)
        if search['photos']:
            img_url = search['photos'][0]['src']['original']
            img_content = requests.get(img_url).content
            with open(f"{topic}_bg.jpg", 'wb') as f:
                f.write(img_content)
        
        # 2. 썸네일 제작
        img = Image.open(f"{topic}_bg.jpg")
        draw = ImageDraw.Draw(img)
        
        # 폰트 설정 (시스템 기본 폰트 사용)
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 50), topic, fill="white", font=font)
        thumbnail_file = f"{topic}_thumbnail.jpg"
        img.save(thumbnail_file)
        
        return thumbnail_file
    except Exception as e:
        print(f"❌ 썸네일 생성 오류: {e}")
        raise
