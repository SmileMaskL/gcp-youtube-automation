import os
import logging
import requests
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, ColorClip
from PIL import Image, ImageDraw, ImageFont
from elevenlabs import generate, save, set_api_key
import numpy as np
import tempfile

logger = logging.getLogger(__name__)

def create_video(script: str, topic: str) -> str:
    try:
        # 1. 폰트 경로 설정 (GitHub 저장소 내 폰트 사용)
        font_path = os.path.join("fonts", "Catfont.ttf")
        if not os.path.exists(font_path):
            logger.warning("⚠️ 사용자 폰트 없음. 시스템 폰트 사용")
            try:
                font = ImageFont.truetype("malgun.ttf", 60)  # Windows
            except:
                font = ImageFont.truetype("AppleGothic", 60)  # Mac
        else:
            font = ImageFont.truetype(font_path, 60)
        
        # 2. 배경 이미지 생성 (Pexels API 사용)
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

        # 3. ElevenLabs 음성 생성
        def generate_audio(text):
            try:
                set_api_key(os.getenv("ELEVENLABS_API_KEY"))
                voice_id = "uyVNoMrnUku1dZyVEXwD"  # 안나 킴
                audio = generate(text=text, voice=voice_id)
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    save(audio, f.name)
                    return f.name
            except Exception as e:
                logger.error(f"⚠️ ElevenLabs 오류: {e}. gTTS로 대체")
                tts = gTTS(text=text, lang='ko', slow=False)
                tts.save("temp_audio.mp3")
                return "temp_audio.mp3"

        # 4. 동적 콘텐츠 생성
        width, height = 1080, 1920  # Shorts 세로 해상도
        audio_path = generate_audio(script)
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        
        # 5. 배경 이미지 다운로드 및 처리
        bg_url = get_background_image()
        if bg_url:
            img_data = requests.get(bg_url).content
            with open("temp_bg.jpg", "wb") as f:
                f.write(img_data)
            bg_image = Image.open("temp_bg.jpg").resize((width, height))
        else:
            bg_image = Image.new('RGB', (width, height), color=(40, 40, 40))  # 어두운 회색 배경
        
        # 6. 텍스트 렌더링 (멀티라인 지원)
        draw = ImageDraw.Draw(bg_image)
        words = script.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            text_bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            if text_width < width - 100:  # 여백 고려
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(current_line.strip())
        
        # 7. 텍스트 위치 계산
        line_height = 70
        y = (height - (len(lines) * line_height)) // 2
        
        for line in lines:
            text_bbox = draw.textbbox((0, 0), line, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            position = ((width - text_width) // 2, y)
            draw.text(position, line, font=font, fill=(255, 255, 255))
            y += line_height
        
        # 8. 동영상 생성
        bg_image.save("temp_frame.jpg")
        clip = ImageClip("temp_frame.jpg").set_duration(duration)
        final_clip = clip.set_audio(audio_clip)
        
        # 9. 출력
        output_path = os.path.join('output', f"{topic.replace(' ', '_')}_shorts.mp4")
        final_clip.write_videofile(
            output_path, 
            fps=24, 
            codec='libx264', 
            audio_codec='aac',
            ffmpeg_params=["-shortest"]  # 오디오 길이에 맞춤
        )
        
        # 10. 임시 파일 정리
        for f in [audio_path, "temp_bg.jpg", "temp_frame.jpg"]:
            if os.path.exists(f):
                os.remove(f)
                
        return output_path
        
    except Exception as e:
        logger.error(f"❌ 동영상 생성 실패: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
