import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class ThumbnailGenerator:
    def __init__(self):
        self.width = 1280
        self.height = 720
        self.font_path = None
        self.setup_fonts()
    
    def setup_fonts(self):
        """폰트 설정"""
        try:
            # 시스템 폰트 경로들
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/System/Library/Fonts/Arial.ttf",
                "/Windows/Fonts/arial.ttf",
                "arial.ttf"
            ]
            
            for path in font_paths:
                if os.path.exists(path):
                    self.font_path = path
                    break
                    
        except Exception as e:
            logger.warning(f"폰트 설정 실패: {e}")
            self.font_path = None
    
    def create_gradient_background(self, color1, color2):
        """그라데이션 배경 생성"""
        try:
            # RGB 색상으로 변환
            r1, g1, b1 = color1
            r2, g2, b2 = color2
            
            # 그라데이션 생성
            background = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            
            for y in range(self.height):
                ratio = y / self.height
                r = int(r1 * (1 - ratio) + r2 * ratio)
                g = int(g1 * (1 - ratio) + g2 * ratio)
                b = int(b1 * (1 - ratio) + b2 * ratio)
                background[y, :] = [b, g, r]  # OpenCV는 BGR 순서
            
            return background
            
        except Exception as e:
            logger.error(f"그라데이션 배경 생성 실패: {e}")
            # 단색 배경으로 대체
            return np.full((self.height, self.width, 3), color1[::-1], dtype=np.uint8)
    
    def add_text_with_outline(self, image, text, position, font_scale=2, 
                            text_color=(255, 255, 255), outline_color=(0, 0, 0),
                            thickness=3, outline_thickness=8):
        """텍스트에 외곽선 추가"""
        try:
            # 외곽선 먼저 그리기
            cv2.putText(image, text, position, cv2.FONT_HERSHEY_SIMPLEX, 
                       font_scale, outline_color, outline_thickness, cv2.LINE_AA)
            
            # 텍스트 그리기
            cv2.putText(image, text, position, cv2.FONT_HERSHEY_SIMPLEX, 
                       font_scale, text_color, thickness, cv2.LINE_AA)
            
        except Exception as e:
            logger.error(f"텍스트 추가 실패: {e}")
    
    def add_shapes_and_effects(self, image):
        """도형과 효과 추가"""
        try:
            # 화살표 추가
            pts = np.array([[100, 300], [200, 250], [200, 280], [300, 280], 
                           [300, 320], [200, 320], [200, 350]], np.int32)
            cv2.fillPoly(image, [pts], (255, 255, 0))  # 노란색 화살표
            
            # 원형 강조 표시
            cv2.circle(image, (1000, 200), 80, (255, 0, 0), 8)  # 빨간색 원
            
            # 느낌표 추가
            cv2.putText(image, "!", (980, 220), cv2.FONT_HERSHEY_SIMPLEX, 
                       3, (255, 0, 0), 8, cv2.LINE_AA)
            
        except Exception as e:
            logger.error(f"도형 추가 실패: {e}")
    
    def create_money_themed_thumbnail(self, title, topic):
        """돈 관련 썸네일 생성"""
        try:
            # 금색 그라데이션 배경
            background = self.create_gradient_background((255, 215, 0), (255, 140, 0))
            
            # 제목 추가 (여러 줄로 분할)
            words = title.split()
            lines = []
            current_line = ""
            
            for word in words:
                if len(current_line + word) < 15:  # 한 줄 최대 길이
                    current_line += word + " "
                else:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + " "
            
            if current_line:
                lines.append(current_line.strip())
            
            # 텍스트 추가
            y_offset = 150
            for i, line in enumerate(lines[:3]):  # 최대 3줄
                y_pos = y_offset + (i * 120)
                self.add_text_with_outline(background, line, (50, y_pos), 
                                         font_scale=1.5, text_color=(0, 0, 0),
                                         outline_color=(255, 255, 255))
            
            # 돈 기호 추가
            self.add_text_with_outline(background, "$$$", (1000, 500), 
                                     font_scale=3, text_color=(0, 255, 0),
                                     outline_color=(0, 0, 0))
            
            # 도형과 효과 추가
            self.add_shapes_and_effects(background)
            
            return background
            
        except Exception as e:
            logger.error(f"돈 테마 썸네일 생성 실패: {e}")
            return self.create_simple_thumbnail(title)
    
    def create_tutorial_thumbnail(self, title, topic):
        """튜토리얼 썸네일 생성"""
        try:
            # 파란색 그라데이션 배경
            background = self.create_gradient_background((30, 144, 255), (0, 100, 200))
            
            # 제목 처리
            main_text = title.split('(')[0].strip()
            
            # 메인 텍스트
            self.add_text_with_outline(background, main_text, (50, 200), 
                                     font_scale=1.8, text_color=(255, 255, 255),
                                     outline_color=(0, 0, 0))
            
            # "HOW TO" 라벨 추가
            cv2.rectangle(background, (50, 50), (300, 120), (255, 0, 0), -1)
            self.add_text_with_outline(background, "HOW TO", (70, 100), 
                                     font_scale=1.2, text_color=(255, 255, 255),
                                     outline_color=(0, 0, 0), thickness=2)
            
            # 체크마크 추가
            pts = np.array([[1000, 400], [1050, 450], [1150, 350]], np.int32)
            cv2.polylines(background, [pts], False, (0, 255, 0), 15)
            
            return background
            
        except Exception as e:
            logger.error(f"튜토리얼 썸네일 생성 실패: {e}")
            return self.create_simple_thumbnail(title)
    
    def create_secret_thumbnail(self, title, topic):
        """비밀/팁 썸네일 생성"""
        try:
            # 어두운 그라데이션 배경
            background = self.create_gradient_background((25, 25, 25), (75, 0, 130))
            
            # "SECRET" 라벨
            cv2.rectangle(background, (50, 50), (250, 120), (255, 0, 255), -1)
            self.add_text_with_outline(background, "SECRET", (70, 100), 
                                     font_scale=1.0, text_color=(255, 255, 255),
                                     outline_color=(0, 0, 0))
            
            # 메인 텍스트
            main_text = title.replace("비밀", "").replace("SECRET", "").strip()
            words = main_text.split()[:4]  # 처음 4단어만
            display_text = " ".join(words)
            
            self.add_text_with_outline(background, display_text, (50, 250), 
                                     font_scale=1.5, text_color=(255, 255, 0),
                                     outline_color=(0, 0, 0))
            
            # 물음표 추가
            self.add_text_with_outline(background, "?", (1100, 300), 
                                     font_scale=4, text_color=(255, 255, 0),
                                     outline_color=(0, 0, 0))
            
            return background
            
        except Exception as e:
            logger.error(f"비밀 썸네일 생성 실패: {e}")
            return self.create_simple_thumbnail(title)
    
    def create_simple_thumbnail(self, title):
        """간단한 썸네일 생성 (기본값)"""
        try:
            # 기본 파란색 배경
            background = np.full((self.height, self.width, 3), (100, 100, 200), dtype=np.uint8)
            
            # 제목을 여러 줄로 분할
            words = title.split()
            lines = []
            current_line = ""
            
            for word in words:
                if len(current_line + word) < 20:
                    current_line += word + " "
                else:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + " "
            
            if current_line:
                lines.append(current_line.strip())
            
            # 텍스트 추가
            y_offset = 200
            for i, line in enumerate(lines[:3]):
                y_pos = y_offset + (i * 100)
                self.add_text_with_outline(background, line, (50, y_pos), 
                                         font_scale=1.3, text_color=(255, 255, 255),
                                         outline_color=(0, 0, 0))
            
            return background
            
        except Exception as e:
            logger.error(f"간단한 썸네일 생성 실패: {e}")
            # 최소한의 썸네일
            return np.full((self.height, self.width, 3), (128, 128, 128), dtype=np.uint8)
    
    def generate_thumbnail(self, title, topic, output_path=None):
        """메인 썸네일 생성 함수"""
        try:
            logger.info(f"썸네일 생성 시작: {title}")
            
            # 키워드에 따라 다른 스타일 적용
            if any(word in title.lower() for word in ['돈', '벌기', '부자', '수익', 'money']):
                thumbnail = self.create_money_themed_thumbnail(title, topic)
            elif any(word in title.lower() for word in ['비밀', '팁', 'secret', '몰랐던']):
                thumbnail = self.create_secret_thumbnail(title, topic)
            elif any(word in title.lower() for word in ['방법', '하는법', 'how', 'tutorial']):
                thumbnail = self.create_tutorial_thumbnail(title, topic)
            else:
                thumbnail = self.create_simple_thumbnail(title)
            
            # 파일 저장
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f'thumbnail_{timestamp}.jpg'
            
            success = cv2.imwrite(output_path, thumbnail)
            
            if success:
                logger.info(f"썸네일 저장 완료: {output_path}")
                return output_path
            else:
                logger.error("썸네일 저장 실패")
                return None
                
        except Exception as e:
            logger.error(f"썸네일 생성 실패: {e}")
            return None
    
    def add_face_placeholder(self, image, position=(800, 200), size=(200, 200)):
        """얼굴 자리표시자 추가 (실제 얼굴 대신)"""
        try:
            x, y = position
            w, h = size
            
            # 원형 배경
            center = (x + w//2, y + h//2)
            cv2.circle(image, center, w//2, (255, 200, 100), -1)
            cv2.circle(image, center, w//2, (0, 0, 0), 5)
            
            # 간단한 얼굴 표시
            # 눈
            cv2.circle(image, (center[0]-30, center[1]-20), 10, (0, 0, 0), -1)
            cv2.circle(image, (center[0]+30, center[1]-20), 10, (0, 0, 0), -1)
            
            # 입
            cv2.ellipse(image, (center[0], center[1]+20), (40, 20), 0, 0, 180, (0, 0, 0), 3)
            
        except Exception as e:
            logger.error(f"얼굴 자리표시자 추가 실패: {e}")

if __name__ == "__main__":
    # 테스트
    generator = ThumbnailGenerator()
    test_title = "유튜브로 월 100만원 벌기 (실제 후기)"
    test_topic = "유튜브 수익화"
    
    result = generator.generate_thumbnail(test_title, test_topic, "test_thumbnail.jpg")
    if result:
        print(f"테스트 썸네일 생성 완료: {result}")
    else:
        print("테스트 썸네일 생성 실패")
