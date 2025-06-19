from PIL import Image, ImageDraw, ImageFont
import os
import logging
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)

def generate_thumbnail(video_path: str, output_thumbnail_path: str, title: str, font_path: str = "/app/fonts/Catfont.ttf"):
    """
    영상에서 스크린샷을 찍고, 제목을 추가하여 썸네일을 생성합니다.
    Args:
        video_path (str): 썸네일을 생성할 비디오 파일 경로.
        output_thumbnail_path (str): 썸네일을 저장할 경로.
        title (str): 썸네일에 들어갈 제목.
        font_path (str): 사용할 폰트 파일 경로.
    """
    logger.info(f"Generating thumbnail for video: {video_path} with title: '{title}'")

    try:
        # 1. 영상에서 프레임 추출 (썸네일 배경)
        clip = VideoFileClip(video_path)
        # 영상 중간 지점의 프레임을 추출
        screenshot_path = "temp_screenshot.png"
        clip.save_frame(screenshot_path, t=clip.duration / 2) # 영상 중간 프레임 저장
        clip.close() # 클립 닫기

        # 2. 이미지 로드 및 크기 조정 (YouTube 권장 썸네일 크기: 1280x720)
        img = Image.open(screenshot_path)
        img = img.resize((1280, 720), Image.LANCZOS) # 고품질 리사이즈
        draw = ImageDraw.Draw(img)

        # 3. 텍스트 추가
        try:
            font_size = 80
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            logger.warning(f"Font not found at {font_path}. Using default font.")
            font = ImageFont.load_default()
            font_size = 50 # 기본 폰트는 크기가 다를 수 있음

        text_color = (255, 255, 255) # 흰색
        stroke_color = (0, 0, 0) # 검은색 테두리
        stroke_width = 3

        # 텍스트를 여러 줄로 나누기 (썸네일에 맞게)
        # 간단한 줄 바꿈 로직
        def wrap_text(text, font, max_width):
            lines = []
            words = text.split(' ')
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                text_width, _ = draw.textsize(test_line, font=font)
                if text_width <= max_width:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            lines.append(' '.join(current_line))
            return "\n".join(lines)

        wrapped_title = wrap_text(title, font, img.width - 100) # 좌우 여백 50px씩

        # 텍스트 위치 계산 (중앙 정렬)
        text_bbox = draw.textbbox((0,0), wrapped_title, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x = (img.width - text_width) / 2
        y = (img.height - text_height) / 2 - 50 # 약간 위로 올림

        # 텍스트와 테두리 그리기
        draw.text((x, y), wrapped_title, font=font, fill=text_color,
                  stroke_width=stroke_width, stroke_fill=stroke_color)

        # 4. 썸네일 저장
        output_dir = os.path.dirname(output_thumbnail_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        img.save(output_thumbnail_path)
        logger.info(f"Thumbnail successfully generated and saved to {output_thumbnail_path}")

    except Exception as e:
        logger.error(f"Failed to generate thumbnail: {e}", exc_info=True)
        raise
    finally:
        # 임시 스크린샷 파일 삭제
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
