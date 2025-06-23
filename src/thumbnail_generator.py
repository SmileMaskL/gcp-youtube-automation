# src/thumbnail_generator.py
import logging
from PIL import Image, ImageDraw, ImageFont
import os # F401 'os' imported but unused -> 실제로 사용되므로 유지

logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    def __init__(self, font_path=None):
        # /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf 는 GCP 빌드 환경에 없을 수 있음.
        # 이를 고려하여 다른 기본 폰트 경로를 사용하거나, 에러 처리 필요.
        # 여기서는 NanumSquare 폰트가 설치되어 있다고 가정.
        # E501 해결: 줄 길이를 79자 이하로 맞춤
        self.font_path = font_path if font_path else "/usr/share/fonts/truetype/" \
                                                     "nanum/NanumSquareB.ttf"
        logger.info(f"ThumbnailGenerator initialized with font: {self.font_path}")

    def create_thumbnail(self, video_title, output_path, resolution=(1280, 720)):
        """
        Creates a custom thumbnail image for a YouTube video.
        """
        try:
            width, height = resolution
            img = Image.new('RGB', (width, height), color=(73, 109, 137))
            d = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype(self.font_path, 80)
            except IOError:
                # E501 해결: 줄 길이를 79자 이하로 맞춤
                logger.warning(f"Font not found at {self.font_path}. "
                               f"Using default font.")
                font = ImageFont.load_default()

            bbox = d.textbbox((0, 0), video_title, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            max_text_width = width * 0.8

            if text_width > max_text_width:
                ratio = max_text_width / text_width
                font_size = int(80 * ratio)
                font = ImageFont.truetype(self.font_path, font_size)
                bbox = d.textbbox((0, 0), video_title, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

            x = (width - text_width) / 2
            y = (height - text_height) / 2 - 50

            d.rectangle([x-20, y-20, x+text_width+20, y+text_height+20], fill=(0, 0, 0, 180))

            d.text((x, y), video_title, font=font, fill=(255, 255, 255))

            img.save(output_path)
            logger.info(f"Thumbnail created successfully: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}", exc_info=True)
            raise
    
