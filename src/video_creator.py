import os
import tempfile
import logging
from moviepy.editor import *
from PIL import Image
import numpy as np
from gtts import gTTS  # ✅ 직접 임포트

logger = logging.getLogger(__name__)

def create_video(script: str, topic: str) -> str:
    try:
        # 1. 음성 생성
        audio_path = "audio.mp3"
        tts = gTTS(text=script, lang='ko', slow=False)
        tts.save(audio_path)
        logger.info("✅ 음성 파일 생성 완료")

        # 2. 동영상 클립 준비
        clips = []
        width, height = 1920, 1080
        
        # 3. OpenCV 시도 (가능한 경우만)
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, (width, height))
                    clips.append(ImageClip(frame).set_duration(5))
                cap.release()
                logger.info("✅ OpenCV 영상 캡처 성공")
        except Exception as e:
            logger.warning(f"⚠️ OpenCV 사용 불가: {e}")
        
        # 4. 기본 영상 생성 (OpenCV 실패 시)
        if not clips:
            color_clip = ColorClip(size=(width, height), color=(0, 0, 0))
            text_clip = TextClip(topic, fontsize=70, color='white', size=(width-100, None))
            text_clip = text_clip.set_position('center').set_duration(5)
            clips = [CompositeVideoClip([color_clip, text_clip])]
            logger.info("✅ 기본 영상 생성 (OpenCV 없음)")
        
        # 5. 음성과 영상 결합
        final_clip = concatenate_videoclips(clips)
        final_clip = final_clip.set_audio(AudioFileClip(audio_path))
        
        # 6. 최종 출력
        output_path = f"{topic.replace(' ', '_')}_final.mp4"
        final_clip.write_videofile(output_path, fps=24)
        logger.info(f"✅ 동영상 저장 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ 동영상 생성 실패: {str(e)}")
        return None
