import os
import logging
# 🔥 여기가 모든 문제의 시작점이었습니다! 아래와 같이 수정했습니다.
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
import numpy as np

logger = logging.getLogger(__name__)

def create_video(script: str, topic: str) -> str:
    try:
        # 1. 음성 생성 (gTTS 사용)
        audio_path = "audio.mp3"
        tts = gTTS(text=script, lang='ko', slow=False)
        tts.save(audio_path)
        logger.info("✅ 음성 파일 생성 완료 (gTTS)")

        # 2. 동영상 프레임 설정
        width, height = 1920, 1080
        
        # 🔥 오디오 길이에 맞춰 동영상 길이를 자동으로 설정합니다.
        audio = AudioFileClip(audio_path)
        duration = audio.duration + 1 # 오디오 길이보다 1초 길게 설정

        # 3. 정적 배경 + 텍스트 영상 생성 (Pillow 사용)
        background = Image.new('RGB', (width, height), color=(20, 20, 20)) # 세련된 검은색
        draw = ImageDraw.Draw(background)

        # 4. 한국어 폰트 설정 (시스템에 없으면 기본 폰트 사용)
        font_path = None
        try:
            # GitHub Actions (Ubuntu) 환경에서는 기본 한국어 폰트가 없습니다.
            # 폰트 파일을 프로젝트에 포함하거나, 아래처럼 기본 폰트를 사용해야 합니다.
            # 여기서는 기본 폰트를 사용하도록 설정합니다.
            font = ImageFont.load_default()
            font_size = 60
            # 만약 특정 폰트를 쓰고 싶다면, .ttf 파일을 프로젝트에 넣고 경로를 지정하세요.
            # font = ImageFont.truetype("fonts/NanumGothic.ttf", 60)
        except Exception:
            font = ImageFont.load_default()
            font_size = 60

        # 5. 텍스트 배치 (가운데 정렬)
        # Pillow 최신 버전에 맞는 getbbox 사용
        text_bbox = draw.textbbox((0, 0), topic, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_position = ((width - text_width) // 2, (height - text_height) // 2)

        draw.text(text_position, topic, font=font, fill=(255, 255, 255))

        # 6. PIL 이미지를 MoviePy 클립으로 변환
        frame = np.array(background)
        clip = ImageClip(frame).set_duration(duration)
        
        # 7. 음성과 영상 결합
        final_clip = clip.set_audio(audio)

        # 8. 파일 저장
        output_path = f"{topic.replace(' ', '_')}_final.mp4"
        final_clip.write_videofile(output_path, fps=24, codec='libx264', logger='bar')
        logger.info(f"✅ 동영상 저장 완료: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"❌ 동영상 생성 실패: {str(e)}")
        # 에러 발생 시 traceback을 함께 기록하여 디버깅 용이하게 함
        import traceback
        logger.error(traceback.format_exc())
        return None
