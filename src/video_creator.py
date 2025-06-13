import os
import logging
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
import numpy as np

logger = logging.getLogger(__name__)

def create_video(script: str, topic: str) -> str:
    try:
        # 1. 음성 생성
        audio_path = "audio.mp3"
        tts = gTTS(text=script, lang='ko', slow=False)
        tts.save(audio_path)
        logger.info("✅ 음성 파일 생성 완료")

        # 2. 동영상 생성
        width, height = 1920, 1080
        duration = 5  # 각 장면 지속 시간 (초)
        clips = []
        
        # 3. 정적 배경 + 텍스트 영상 생성
        background = Image.new('RGB', (width, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(background)
        
        # 한국어 폰트 설정
        try:
            font = ImageFont.truetype("malgun.ttf", 60)  # Windows
        except:
            try:
                font = ImageFont.truetype("NanumGothic.ttf", 60)  # Linux
            except:
                font = ImageFont.load_default()
        
        # 텍스트 크기 계산 및 위치 조정
        text_bbox = draw.textbbox((0, 0), topic, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_position = ((width - text_width) // 2, (height - text_height) // 2)
        
        draw.text(text_position, topic, font=font, fill=(255, 255, 255))
        
        # PIL 이미지 → NumPy 배열 → MoviePy 클립
        frame = np.array(background)
        clip = ImageClip(frame).set_duration(duration)
        clips.append(clip)
        
        # 4. 음성과 영상 결합
        final_clip = concatenate_videoclips(clips)
        audio_clip = AudioFileClip(audio_path)
        final_clip = final_clip.set_audio(audio_clip)
        
        # 5. 파일 저장
        output_path = f"{topic.replace(' ', '_')}_final.mp4"
        final_clip.write_videofile(output_path, fps=24, codec='libx264')
        logger.info(f"✅ 동영상 저장 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ 동영상 생성 실패: {str(e)}")
        return None
