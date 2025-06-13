# src/video_creator.py

import os
import logging
import requests
import tempfile
from moviepy.editor import ImageClip, AudioFileClip
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
import numpy as np

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 💡 환경 변수는 반드시 .env 또는 GitHub Actions에서 설정해야 함
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# 🎬 메인 함수
def create_video(script: str, topic: str) -> str:
    try:
        # 1. 폰트 설정 (중학생도 이해 가능!)
        try:
            font_path = "fonts/Catfont.ttf"
            font = ImageFont.truetype(font_path, 60)
        except:
            font = ImageFont.load_default()
            logger.warning("⚠️ 사용자 정의 폰트 없음. 기본 폰트 사용")

        # 2. PEXELS에서 배경 이미지 불러오기
        def get_background_image():
            try:
                headers = {"Authorization": PEXELS_API_KEY}
                params = {"query": topic, "per_page": 1}
                response = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return data["photos"][0]["src"]["large"]
            except Exception as e:
                logger.error(f"⚠️ 배경 이미지 불러오기 실패: {e}")
            return None

        # 3. ElevenLabs 또는 gTTS로 오디오 생성
        def generate_audio(text):
            try:
                import elevenlabs
                audio = elevenlabs.generate(
                    text=text,
                    voice="uyVNoMrnUku1dZyVEXwD",
                    model="eleven_multilingual_v2",
                    api_key=ELEVEN_API_KEY
                )
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    f.write(audio)
                    return f.name
            except Exception as e:
                logger.warning(f"⚠️ ElevenLabs 실패: {e}, gTTS 대체")
                tts = gTTS(text=text, lang='ko')
                tts_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
                tts.save(tts_path)
                return tts_path

        # 4. 배경 이미지 만들기
        bg_url = get_background_image()
        width, height = 1080, 1920
        if bg_url:
            response = requests.get(bg_url)
            bg_image = Image.open(tempfile.NamedTemporaryFile(delete=False).name)
            bg_image = Image.open(requests.get(bg_url, stream=True).raw).resize((width, height))
        else:
            bg_image = Image.new("RGB", (width, height), color=(30, 30, 30))

        # 5. 텍스트 나누기
        draw = ImageDraw.Draw(bg_image)
        words = script.split()
        lines, current_line = [], ""
        for word in words:
            test_line = current_line + word + " "
            if draw.textbbox((0, 0), test_line, font=font)[2] < width - 100:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(current_line.strip())

        # 6. 텍스트 중앙 정렬해서 이미지 위에 쓰기
        y = (height - len(lines) * 70) // 2
        for line in lines:
            w = draw.textbbox((0, 0), line, font=font)[2]
            draw.text(((width - w) // 2, y), line, font=font, fill="white")
            y += 70

        # 7. 이미지 저장 & 오디오 불러오기
        frame_path = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False).name
        bg_image.save(frame_path)
        audio_path = generate_audio(script)
        audio_clip = AudioFileClip(audio_path)

        # 8. 영상 만들기
        clip = ImageClip(frame_path).set_duration(audio_clip.duration).set_audio(audio_clip)
        output_path = os.path.join("output", f"{topic.replace(' ', '_')}_shorts.mp4")
        clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac', ffmpeg_params=["-shortest"])

        # 9. 정리
        for f in [frame_path, audio_path]:
            if os.path.exists(f):
                os.remove(f)

        return output_path

    except Exception as e:
        logger.error(f"❌ 영상 생성 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
