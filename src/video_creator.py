# src/video_creator.py

import os
import logging
import requests
from moviepy.editor import ImageClip, AudioFileClip
from PIL import Image, ImageDraw, ImageFont
from elevenlabs.client import ElevenLabs     # ✅ 여기를 수정했습니다!
import numpy as np
import tempfile
logger = logging.getLogger(__name__)

def create_video(script: str, topic: str) -> str:
    try:
        # (1) 폰트
        font_path = os.path.join("fonts", "Catfont.ttf")
        if not os.path.exists(font_path):
            logger.warning("⚠️ 사용자 폰트 없음. 시스템 폰트 사용")
            try:
                font = ImageFont.truetype("malgun.ttf", 60)
            except:
                font = ImageFont.truetype("AppleGothic", 60)
        else:
            font = ImageFont.truetype(font_path, 60)

        # (2) 배경 이미지 함수
        def get_background_image():
            try:
                api_key = os.getenv("PEXELS_API_KEY")
                if api_key:
                    headers = {"Authorization": api_key}
                    params = {"query": topic, "per_page": 1}
                    response = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        if data['photos']:
                            return data['photos'][0]['src']['large']
            except Exception as e:
                logger.error(f"⚠️ 배경 이미지 오류: {e}")
            return None

        # (3) ElevenLabs 음성 생성 - 수정된 부분 시작
        def generate_audio(text):
            try:
                eleven_api_key = os.getenv("ELEVENLABS_API_KEY")
                client = ElevenLabs(api_key=eleven_api_key)

                voice_id = "uyVNoMrnUku1dZyVEXwD"
                audio = client.generate(text=text, voice=voice_id, model="eleven_multilingual_v2")

                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    f.write(audio)
                    return f.name

            except Exception as e:
                logger.error(f"⚠️ ElevenLabs 오류: {e}. gTTS로 대체")
                from gtts import gTTS
                tts = gTTS(text=text, lang='ko', slow=False)
                tts.save("temp_audio.mp3")
                return "temp_audio.mp3"
        # 수정된 부분 끝

        # (4) 동영상 생성
        width, height = 1080, 1920
        audio_path = generate_audio(script)
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        # (5) 배경 처리
        bg_url = get_background_image()
        if bg_url:
            img_data = requests.get(bg_url).content
            with open("temp_bg.jpg", "wb") as f:
                f.write(img_data)
            bg_image = Image.open("temp_bg.jpg").resize((width, height))
        else:
            bg_image = Image.new('RGB', (width, height), color=(40, 40, 40))

        # (6) 텍스트 나누기
        draw = ImageDraw.Draw(bg_image)
        words = script.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            text_bbox = draw.textbbox((0, 0), test_line, font=font)
            if text_bbox[2] - text_bbox[0] < width - 100:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(current_line.strip())

        # (7) 텍스트 위치 그리기
        line_height = 70
        y = (height - (len(lines) * line_height)) // 2
        for line in lines:
            text_bbox = draw.textbbox((0, 0), line, font=font)
            position = ((width - (text_bbox[2] - text_bbox[0])) // 2, y)
            draw.text(position, line, font=font, fill=(255, 255, 255))
            y += line_height

        # (8) 영상 생성
        bg_image.save("temp_frame.jpg")
        clip = ImageClip("temp_frame.jpg").set_duration(duration).set_audio(audio_clip)

        # (9) 결과 저장
        output_path = os.path.join('output', f"{topic.replace(' ', '_')}_shorts.mp4")
        clip.write_videofile(output_path, fps=24, codec='libx264',
                             audio_codec='aac', ffmpeg_params=["-shortest"])

        # (10) 정리
        for f in [audio_path, "temp_bg.jpg", "temp_frame.jpg"]:
            if os.path.exists(f):
                os.remove(f)

        return output_path

    except Exception as e:
        logger.error(f"❌ 동영상 생성 실패: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
