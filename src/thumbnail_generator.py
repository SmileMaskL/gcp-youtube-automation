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
        self.colors = [
            (255, 87, 51),   # 빨간색
            (255, 193, 7),   # 노란색
            (40, 167, 69),   # 초록색
            (0, 123, 255),   # 파란색
            (108, 117, 125), # 회색
            (220, 53, 69),   # 진한 빨간색
            (255, 193, 7),   # 주황색
        ]
        
    def create_thumbnail(self, title, subtitle="", output_path="thumbnail.jpg"):
        """썸네일 이미지 생성"""
        try:
            # 배경 이미지 생성
            img = Image.new('RGB', (self.width, self.height), color=(33, 37, 41))
            draw = ImageDraw.Draw(img)
            
            # 그라데이션 배경 추가
            self._add_gradient_background(img)
            
            # 제목 추가
            self._add_title_text(draw, title)
            
            # 부제목 추가
            if subtitle:
                self._add_subtitle_text(draw, subtitle)
            
            # 장식 요소 추가
            self._add_decorative_elements(draw)
            
            # 이미지 저장
            img.save(output_path, quality=95)
            logger.info(f"썸네일 생성 완료: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"썸네일 생성 실패: {str(e)}")
            raise
    
    def _add_gradient_background(self, img):
        """그라데이션 배경 추가"""
        try:
            # 선택한 색상으로 그라데이션 생성
            color = random.choice(self.colors)
            
            # 배경 그라데이션
            for y in range(self.height):
                # 위에서 아래로 어두워지는 그라데이션
                alpha = y / self.height
                dark_factor = 0.3 + (0.7 * alpha)
                
                current_color = (
                    int(color[0] * dark_factor),
                    int(color[1] * dark_factor),
                    int(color[2] * dark_factor)
                )
                
                # 한 줄씩 그리기
                for x in range(self.width):
                    img.putpixel((x, y), current_color)
                    
        except Exception as e:
            logger.error(f"배경 생성 실패: {str(e)}")
    
    def _add_title_text(self, draw, title):
        """제목 텍스트 추가"""
        try:
            # 폰트 크기 설정
            font_size = 80
            
            # 기본 폰트 사용 (시스템에 따라 다름)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # 텍스트 길이에 따라 폰트 크기 조정
            while len(title) * font_size > self.width * 0.8:
                font_size -= 5
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
                except:
                    try:
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
            
            # 텍스트 위치 계산
            bbox = draw.textbbox((0, 0), title, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (self.width - text_width) // 2
            y = (self.height - text_height) // 2 - 50
            
            # 텍스트 그림자 효과
            shadow_offset = 3
            draw.text((x + shadow_offset, y + shadow_offset), title, font=font, fill=(0, 0, 0, 128))
            
            # 메인 텍스트
            draw.text((x, y), title, font=font, fill=(255, 255, 255))
            
        except Exception as e:
            logger.error(f"제목 텍스트 추가 실패: {str(e)}")
    
    def _add_subtitle_text(self, draw, subtitle):
        """부제목 텍스트 추가"""
        try:
            font_size = 40
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # 텍스트 위치 계산
            bbox = draw.textbbox((0, 0), subtitle, font=font)
            text_width = bbox[2] - bbox[0]
            
            x = (self.width - text_width) // 2
            y = self.height // 2 + 100
            
            # 배경 박스
            padding = 10
            box_coords = [
                x - padding,
                y - padding,
                x + text_width + padding,
                y + font_size + padding
            ]
            draw.rectangle(box_coords, fill=(0, 0, 0, 100))
            
            # 부제목 텍스트
            draw.text((x, y), subtitle, font=font, fill=(255, 255, 255))
            
        except Exception as e:
            logger.error(f"부제목 텍스트 추가 실패: {str(e)}")
    
    def _add_decorative_elements(self, draw):
        """장식 요소 추가"""
        try:
            # 모서리에 작은 원들 추가
            circle_color = random.choice(self.colors)
            
            # 좌상단
            draw.ellipse([20, 20, 80, 80], fill=circle_color)
            
            # 우상단
            draw.ellipse([self.width-80, 20, self.width-20, 80], fill=circle_color)
            
            # 좌하단
            draw.ellipse([20, self.height-80, 80, self.height-20], fill=circle_color)
            
            # 우하단
            draw.ellipse([self.width-80, self.height-80, self.width-20, self.height-20], fill=circle_color)
            
            # 중앙 상단에 강조 라인
            line_y = 100
            draw.rectangle([self.width//2 - 150, line_y, self.width//2 + 150, line_y + 8], fill=(255, 255, 255))
            
        except Exception as e:
            logger.error(f"장식 요소 추가 실패: {str(e)}")
    
    def create_multiple_thumbnails(self, title, count=3):
        """여러 버전의 썸네일 생성"""
        thumbnails = []
        
        for i in range(count):
            output_path = f"thumbnail_{i+1}.jpg"
            
            # 각각 다른 스타일로 생성
            if i == 0:
                # 기본 스타일
                thumbnail_path = self.create_thumbnail(title, "", output_path)
            elif i == 1:
                # 부제목 포함
                subtitle = "💰 월 100만원 달성법"
                thumbnail_path = self.create_thumbnail(title, subtitle, output_path)
            else:
                # 다른 색상 스킴
                original_colors = self.colors.copy()
                self.colors = [(255, 20, 147), (138, 43, 226), (30, 144, 255)]  # 핑크/보라/파랑 계열
                thumbnail_path = self.create_thumbnail(title, "🔥 실제 후기", output_path)
                self.colors = original_colors
            
            thumbnails.append(thumbnail_path)
            
        return thumbnails
