# src/video_creator.py (수정 버전)

import os
import logging
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, ColorClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import requests
from elevenlabs import generate, save, set_api_key
from gtts import gTTS  # fallback으로 사용

logger = logging.getLogger(__name__)

def create_video(script: str, topic: str) -> str:
    try:
        # 0. 환경 변수 로드
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        pexels_api_key = os.getenv("PEXELS_API_KEY")
        
        # 1. 배경 이미지 생성 (Pexels에서 주제로 검색)
        bg_image_path = f"{topic}_bg.jpg"
        if pexels_api_key:
            try:
                headers = {"Authorization": pexels_api_key}
                params = {"query": topic, "per_page": 1}
                response = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data['photos']:
                        img_url = data['photos'][0]['src']['original']
                        img_content = requests.get(img_url).content
                        with open(bg_image_path, 'wb') as f:
                            f.write(img_content)
            except Exception as e:
                logger.error(f"Pexels 이미지 다운로드 실패: {e}")
        
        # 2. 음성 생성 (ElevenLabs 사용)
        audio_path = "temp_audio.mp3"
        if elevenlabs_api_key:
            try:
                set_api_key(elevenlabs_api_key)
                voice_id = "uyVNoMrnUku1dZyVEXwD"  # 안나 킴
                audio = generate(text=script, voice=voice_id)
                save(audio, audio_path)
                logger.info("✅ ElevenLabs 음성 파일 생성 완료")
            except Exception as e:
                logger.error(f"ElevenLabs 음성 생성 실패: {e}. gTTS로 대체합니다.")
                tts = gTTS(text=script, lang='ko', slow=False)
                tts.save(audio_path)
        else:
            tts = gTTS(text=script, lang='ko', slow=False)
            tts.save(audio_path)
        
        # 3. 동영상 프레임 설정 (세로 해상도: 1080x1920)
        width, height = 1080, 1920
        
        # 오디오 길이에 맞춰 동영상 길이 설정
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        
        # 4. 배경 이미지 로드 및 리사이즈
        try:
            img = Image.open(bg_image_path).resize((width, height))
        except:
            img = Image.new('RGB', (width, height), color=(20, 20, 20))
        
        draw = ImageDraw.Draw(img)
        
        # 5. 한국어 폰트 설정 (사용자 지정 폰트 사용)
        try:
            # 사용자가 제공한 폰트 사용
            font_path = "fonts/Catfont.ttf"
            font = ImageFont.truetype(font_path, 60)
        except Exception as e:
            logger.error(f"사용자 폰트 로드 실패: {e}. 기본 폰트 사용")
            try:
                font = ImageFont.truetype("malgun.ttf", 60)  # Windows
            except:
                font = ImageFont.truetype("AppleGothic", 60)  # Mac
                # 최종 대체: Pillow의 기본 폰트
                if not font:
                    font = ImageFont.load_default().font_variant(size=60)
        
        # 6. 텍스트를 이미지 중앙에 배치
        # 스크립트를 여러 줄로 분할
        words = script.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            text_width = draw.textbbox((0, 0), test_line, font=font)[2] - draw.textbbox((0, 0), test_line, font=font)[0]
            if text_width < width - 100:  # 여백 고려
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(current_line.strip())
        
        # 줄 간격 설정
        line_height = 70
        y = (height - (len(lines) * line_height)) // 2
        
        for line in lines:
            text_bbox = draw.textbbox((0, 0), line, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            position = ((width - text_width) // 2, y)
            draw.text(position, line, font=font, fill=(255, 255, 255))
            y += line_height
        
        # PIL 이미지를 MoviePy 클립으로 변환
        frame = np.array(img)
        clip = ImageClip(frame).set_duration(duration)
        
        # 7. 음성과 영상 결합
        final_clip = clip.set_audio(audio)
        
        # 8. 파일 저장
        if not os.path.exists('output'):
            os.makedirs('output')
        output_path = os.path.join('output', f"{topic.replace(' ', '_')}_shorts.mp4")
        
        final_clip.write_videofile(output_path, fps=24, codec='libx264', logger='bar')
        logger.info(f"✅ Shorts 동영상 저장 완료: {output_path}")
        
        # 임시 파일 삭제
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(bg_image_path):
            os.remove(bg_image_path)
        
        return output_path
        
    except Exception as e:
        logger.error(f"❌ 동영상 생성 실패: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
