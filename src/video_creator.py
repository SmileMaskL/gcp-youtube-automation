# src/video_creator.py (전체 코드)

import os
import logging
# 🔥 여기가 모든 문제의 원흉! 이렇게 필요한 것만 콕 집어 불러와야 합니다.
from moviepy.editor import ImageClip, AudioFileClip
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
import numpy as np

logger = logging.getLogger(__name__)

def create_video(script: str, topic: str) -> str:
    try:
        # 1. 음성 생성 (gTTS 사용)
        audio_path = os.path.join("temp_audio.mp3") # 파일 경로를 명확히 함
        tts = gTTS(text=script, lang='ko', slow=False)
        tts.save(audio_path)
        logger.info("✅ 음성 파일 생성 완료 (gTTS)")

        # 2. 동영상 프레임 설정
        width, height = 1920, 1080
        
        # 🔥 오디오 길이에 맞춰 동영상 길이를 자동으로 설정
        audio = AudioFileClip(audio_path)
        duration = audio.duration + 1 # 오디오 길이보다 1초 여유

        # 3. 정적 배경 + 텍스트 영상 생성 (Pillow 사용)
        background = Image.new('RGB', (width, height), color=(20, 20, 20)) # 세련된 다크 그레이
        draw = ImageDraw.Draw(background)

        # 4. 한국어 폰트 설정 (GitHub Actions 환경에서는 기본 폰트만 사용 가능)
        try:
            # 폰트 파일을 프로젝트에 포함시키면 더 예쁜 폰트 사용 가능
            # 예: font = ImageFont.truetype("fonts/NanumGothicBold.ttf", 60)
            font = ImageFont.load_default().font_variant(size=60)
        except Exception:
            font = ImageFont.load_default()
        
        # 5. 텍스트를 이미지 중앙에 배치
        text_bbox = draw.textbbox((0, 0), topic, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        position = ((width - text_width) // 2, (height - text_height) // 2)

        draw.text(position, topic, font=font, fill=(255, 255, 255))

        # 6. PIL 이미지를 MoviePy 클립으로 변환
        frame = np.array(background)
        clip = ImageClip(frame).set_duration(duration)
        
        # 7. 음성과 영상 결합
        final_clip = clip.set_audio(audio)

        # 8. 파일 저장 (출력 폴더를 만들면 더 깔끔)
        if not os.path.exists('output'):
            os.makedirs('output')
        output_path = os.path.join('output', f"{topic.replace(' ', '_')}_final.mp4")
        
        final_clip.write_videofile(output_path, fps=24, codec='libx264', logger='bar')
        logger.info(f"✅ 동영상 저장 완료: {output_path}")

        # 임시 오디오 파일 삭제
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return output_path

    except Exception as e:
        logger.error(f"❌ 동영상 생성 실패: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
