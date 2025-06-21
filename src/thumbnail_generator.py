# src/thumbnail_generator.py
import logging
import os
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

class ThumbnailGenerator:
    def __init__(self, font_path: str):
        self.font_path = font_path
        if not os.path.exists(self.font_path):
            logger.error(f"Font file not found at {self.font_path}. Thumbnail creation might fail or use default font.")

    def generate_thumbnail(self, text_content: str, output_path: str, width: int = 1280, height: int = 720) -> bool:
        """
        주어진 텍스트로 썸네일 이미지를 생성합니다.
        
        Args:
            text_content (str): 썸네일에 표시할 텍스트.
            output_path (str): 썸네일 이미지 저장 경로.
            width (int): 썸네일 너비.
            height (int): 썸네일 높이.

        Returns:
            bool: 썸네일 생성 성공 여부.
        """
        try:
            img = Image.new('RGB', (width, height), color = (73, 109, 137))
            d = ImageDraw.Draw(img)

            try:
                # 폰트 로드 (고양이체.ttf)
                font_size = 80
                fnt = ImageFont.truetype(self.font_path, font_size)
            except IOError:
                logger.warning(f"Could not load font from {self.font_path}. Using default font.")
                fnt = ImageFont.load_default()
                font_size = 40 # 기본 폰트의 경우 크기 조절

            # 텍스트 자동 줄바꿈 및 중앙 정렬
            lines = []
            words = text_content.split()
            current_line = []
            for word in words:
                test_line = " ".join(current_line + [word])
                text_width, text_height = d.textbbox((0,0), test_line, font=fnt)[2:]
                if text_width < width * 0.8: # 이미지 너비의 80% 안에 들어오도록
                    current_line.append(word)
                else:
                    lines.append(" ".join(current_line))
                    current_line = [word]
            lines.append(" ".join(current_line))

            y_text = height / 2 - (len(lines) * font_size / 2) # 시작 y 위치 조정
            
            for line in lines:
                text_width, text_height = d.textbbox((0,0), line, font=fnt)[2:]
                x_text = (width - text_width) / 2 # 중앙 정렬
                d.text((x_text, y_text), line, font=fnt, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
                y_text += text_height * 1.2 # 다음 줄로 이동

            img.save(output_path)
            logger.info(f"Thumbnail successfully generated at {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}", exc_info=True)
            return False
