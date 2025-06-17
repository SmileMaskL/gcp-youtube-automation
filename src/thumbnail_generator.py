"""
썸네일 생성 모듈 (최종 수정본)
"""
import os
import logging
from PIL import Image, ImageDraw, ImageFont
import cv2

logger = logging.getLogger(__name__)

def create_thumbnail(title: str, background_path: str, output_path: str):
    """동영상 프레임을 캡처하여 썸네일 생성"""
    try:
        # 1. 동영상에서 첫 프레임 캡처
        vidcap = cv2.VideoCapture(background_path)
        success, image = vidcap.read()
        if not success:
            raise ValueError("동영상에서 프레임을 읽을 수 없습니다")
        
        # 임시 프레임 저장
        frame_path = os.path.join(os.path.dirname(output_path), "temp_frame.jpg")
        cv2.imwrite(frame_path, image)
        
        # 2. 이미지 열기 (이 부분이 추가되었습니다!)
        img = Image.open(frame_path)
        img = img.resize((1080, 1920))  # 쇼츠 사이즈
        
        # 3. 제목 추가
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("fonts/Catfont.ttf", 80)
        except:
            font = ImageFont.load_default()
        
        # 제목 배경 (반투명)
        draw.rectangle([(50, 1400), (1030, 1600)], fill=(0, 0, 0, 128))
        
        # 제목 텍스트
        draw.text((540, 1500), title, font=font, fill=(255, 255, 255), anchor="mm")
        
        # 4. 저장
        img.save(output_path)
        logger.info(f"썸네일 생성 완료: {output_path}")
        
        # 임시 파일 삭제
        os.remove(frame_path)
        
    except Exception as e:
        logger.error(f"썸네일 생성 실패: {e}")
        raise
