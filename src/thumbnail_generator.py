from PIL import Image, ImageDraw, ImageFont
import os
import logging

logger = logging.getLogger(__name__)

def generate_thumbnail(title: str, output_path: str, font_path: str = "fonts/Catfont.ttf"):
    try:
        # 쇼츠 썸네일 크기: 1280x720 또는 1920x1080 (비율 유지)
        # 유튜브 쇼츠는 세로 영상이므로, 썸네일도 세로 비율을 고려하는 것이 좋음.
        # 일반적으로 1280x720 (가로) 썸네일도 쇼츠에서 잘 표시됨.
        # 여기서는 쇼츠의 일반적인 세로 비율을 고려하여 720x1280 (세로)로 생성합니다.
        width, height = 720, 1280
        img = Image.new('RGB', (width, height), color = (0, 0, 0)) # 검은색 배경
        d = ImageDraw.Draw(img)

        try:
            # 요청하신 Catfont.ttf 사용
            font = ImageFont.truetype(font_path, 60)
        except IOError:
            logger.warning(f"폰트 파일 '{font_path}'를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
            font = ImageFont.load_default()
            
        # 텍스트를 여러 줄로 나누기
        def wrap_text(text, font, max_width):
            lines = []
            if not text:
                return [""]
            words = text.split(' ')
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                if font.getlength(test_line) <= max_width:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            lines.append(' '.join(current_line))
            return lines

        wrapped_title = wrap_text(title, font, width - 40) # 좌우 여백 20px씩

        y_text = height / 2 - (len(wrapped_title) * font.size) / 2 # 세로 중앙 정렬

        for line in wrapped_title:
            bbox = d.textbbox((0,0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x_text = (width - line_width) / 2 # 가로 중앙 정렬
            d.text((x_text, y_text), line, font=font, fill=(255, 255, 255)) # 흰색 텍스트
            y_text += font.size + 10 # 줄 간격

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
        logger.info(f"썸네일 생성 완료: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"썸네일 생성 실패: {e}")
        return None
