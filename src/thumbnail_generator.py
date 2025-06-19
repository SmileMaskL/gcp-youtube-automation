from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
from src.config import THUMBNAIL_DIR, FONT_PATH
from src.monitoring import log_system_health

def create_thumbnail(text, background_image_path, output_filename="thumbnail.jpg"):
    """
    제공된 텍스트와 배경 이미지를 사용하여 YouTube 썸네일을 생성합니다.
    """
    output_path = os.path.join(THUMBNAIL_DIR, output_filename)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        # 배경 이미지 로드 및 리사이징 (1280x720 또는 1920x1080 추천)
        background = Image.open(background_image_path).convert("RGB")
        # YouTube Shorts는 세로형 (9:16)이므로, 썸네일은 1280x720 (16:9)으로 생성하는 것이 일반적
        # 또는 Shorts에 맞춰 720x1280 (세로) 썸네일도 가능
        # 여기서는 일반적인 YouTube 썸네일 비율 (16:9)을 따릅니다.
        target_width, target_height = 1280, 720
        background = background.resize((target_width, target_height), Image.Resampling.LANCZOS)

        draw = ImageDraw.Draw(background)

        # 폰트 로드
        try:
            # 폰트 경로를 절대 경로 또는 정확한 상대 경로로 지정
            font_size = 80
            font = ImageFont.truetype(FONT_PATH, font_size)
        except IOError:
            log_system_health(f"폰트 파일을 찾을 수 없습니다: {FONT_PATH}. 기본 폰트 사용.", level="warning")
            font = ImageFont.load_default()
            font_size = 60 # 기본 폰트 크기 조정

        # 텍스트 색상 및 외곽선
        text_color = (255, 255, 255)  # 흰색
        stroke_color = (0, 0, 0)      # 검은색
        stroke_width = 5

        # 텍스트 중앙 정렬
        # 텍스트를 여러 줄로 나누는 함수 (PIL 폰트의 textlength 계산 사용)
        def wrap_text(text, font, max_width):
            lines = []
            words = text.split()
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

        # 썸네일 중앙에 텍스트 배치 (가로폭의 80% 사용)
        max_text_width = target_width * 0.8
        wrapped_text = wrap_text(text, font, max_text_width)

        # 각 줄의 높이 계산
        line_heights = [font.getbbox(line)[3] - font.getbbox(line)[1] for line in wrapped_text] # top, left, bottom, right
        total_text_height = sum(line_heights) + (len(wrapped_text) - 1) * 10 # 줄 간 간격 10px

        # 시작 Y 좌표 (중앙 정렬)
        y_text = (target_height - total_text_height) / 2

        for line in wrapped_text:
            text_width = font.getlength(line)
            x_text = (target_width - text_width) / 2

            # 텍스트 외곽선 그리기
            for x_offset in [-stroke_width, 0, stroke_width]:
                for y_offset in [-stroke_width, 0, stroke_width]:
                    if x_offset == 0 and y_offset == 0:
                        continue
                    draw.text((x_text + x_offset, y_text + y_offset), line, font=font, fill=stroke_color)

            # 실제 텍스트 그리기
            draw.text((x_text, y_text), line, font=font, fill=text_color)
            y_text += font.getbbox(line)[3] - font.getbbox(line)[1] + 10 # 다음 줄 시작 위치

        background.save(output_path)
        log_system_health(f"썸네일이 성공적으로 생성되었습니다: {output_path}", level="info")
        return output_path
    except Exception as e:
        log_system_health(f"썸네일 생성 중 오류 발생: {e}", level="error")
        raise ValueError(f"썸네일 생성 실패: {e}")

# For local testing (optional)
if __name__ == "__main__":
    # 테스트를 위해 dummy background.jpg 파일을 생성하거나 준비해야 합니다.
    # 예시: 임시 이미지 생성
    dummy_bg_path = "output/backgrounds/dummy_bg.jpg"
    Path(dummy_bg_path).parent.mkdir(parents=True, exist_ok=True)
    dummy_img = Image.new('RGB', (1280, 720), color = (73, 109, 137))
    dummy_img.save(dummy_bg_path)

    try:
        test_text = "✨오늘의 충격 사실!✨"
        thumbnail_path = create_thumbnail(test_text, dummy_bg_path, "test_thumbnail.jpg")
        print(f"Test thumbnail saved to: {thumbnail_path}")
    except ValueError as e:
        print(f"Error during test: {e}")
