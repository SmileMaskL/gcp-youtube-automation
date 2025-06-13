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

        # 2. 동영상 생성 (OpenCV 없이 Pillow 사용)
        width, height = 1920, 1080
        duration = 5  # 초 단위
        
        # 3. 정적 배경 + 텍스트 영상 생성
        clips = []
        background = Image.new('RGB', (width, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(background)
        
        # 한국어 폰트 설정 (기본 폰트 사용)
        try:
            font = ImageFont.truetype("malgun.ttf", 60)  # Windows 기본 폰트
        except:
            font = ImageFont.load_default()
        
        text_width, text_height = draw.textsize(topic, font=font)
        text_position = ((width - text_width) // 2, (height - text_height) // 2)
        draw.text(text_position, topic, font=font, fill=(255, 255, 255))
        
        # PIL 이미지를 NumPy 배열로 변환 → ImageClip으로 변환
        frame = np.array(background)
        clip = ImageClip(frame).set_duration(duration)
        clips.append(clip)
        
        # 4. 음성과 영상 결합
        final_clip = concatenate_videoclips(clips)
        final_clip = final_clip.set_audio(AudioFileClip(audio_path))
        
        # 5. 파일 저장
        output_path = f"{topic.replace(' ', '_')}_final.mp4"
        final_clip.write_videofile(output_path, fps=24)
        logger.info(f"✅ 동영상 저장 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ 동영상 생성 실패: {str(e)}")
        return None
