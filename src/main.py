import os
import uuid
import random
import requests
from pathlib import Path
from moviepy.editor import (
    ColorClip,
    CompositeVideoClip,
    VideoFileClip,
    AudioFileClip,
    TextClip
)
import logging
from dotenv import load_dotenv
from gtts import gTTS
import google.generativeai as genai
from moviepy.config import change_settings
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import subprocess

# ✅ 필수 시스템 설정
change_settings({
    "IMAGEMAGICK_BINARY": "/usr/bin/convert",
    "FFMPEG_BINARY": "/usr/bin/ffmpeg"
})

# ✅ 환경 변수 로드
load_dotenv()

# ✅ 설정
class Config:
    TEMP_DIR = Path("temp")
    OUTPUT_DIR = Path("output")
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    FONT = "Arial-Unicode-MS"  # 더 보편적인 폰트
    
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ✅ 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ ImageMagick 보안 정책 수정 함수
def fix_imagemagick_policy():
    try:
        policy_file = "/etc/ImageMagick-6/policy.xml"
        if os.path.exists(policy_file):
            with open(policy_file, "r") as f:
                content = f.read()
            
            # 보안 정책 완화
            content = content.replace(
                '<policy domain="coder" rights="none" pattern="PDF" />',
                '<policy domain="coder" rights="read|write" pattern="PDF" />')
            content = content.replace(
                '<policy domain="coder" rights="none" pattern="LABEL" />',
                '<policy domain="coder" rights="read|write" pattern="LABEL" />')
            
            with open(policy_file, "w") as f:
                f.write(content)
            
            logger.info("✅ ImageMagick 보안 정책 수정 완료")
    except Exception as e:
        logger.warning(f"⚠️ ImageMagick 정책 수정 실패: {e}")

# ✅ TTS 생성 (ElevenLabs + gTTS 대체)
def generate_tts(script: str) -> str:
    try:
        # ElevenLabs 시도
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        api_key = os.getenv("ELEVENLABS_API_KEY")
        
        if not api_key:
            raise Exception("ElevenLabs API 키가 없습니다")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        json_data = {
            "text": script,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        response = requests.post(url, headers=headers, json=json_data, timeout=30)
        if response.status_code != 200:
            raise Exception(f"ElevenLabs 실패: {response.status_code}")

        audio_path = Config.TEMP_DIR / f"audio_{uuid.uuid4()}.mp3"
        with open(audio_path, "wb") as f:
            f.write(response.content)

        logger.info(f"🔊 ElevenLabs 음성 생성 완료: {audio_path}")
        return str(audio_path)
    except Exception as e:
        logger.warning(f"[ElevenLabs 실패] {e}, gTTS로 대체")
        try:
            audio_path = Config.TEMP_DIR / f"gtts_{uuid.uuid4()}.mp3"
            tts = gTTS(text=script, lang='ko', slow=False)
            tts.save(str(audio_path))
            logger.info(f"🔊 gTTS 음성 생성 완료: {audio_path}")
            return str(audio_path)
        except Exception as e:
            logger.error(f"[gTTS 실패] {e}")
            raise Exception("모든 TTS 생성 실패")

# ✅ 배경 영상 생성 (Pexels + 대체)
def get_background_video(query: str, duration: int) -> str:
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            raise Exception("Pexels API 키가 없습니다")

        headers = {"Authorization": api_key}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=5&size=small"
        response = requests.get(url, headers=headers, timeout=15)
        videos = response.json().get('videos', [])
        
        if not videos:
            raise Exception("Pexels에서 동영상을 찾을 수 없음")

        # 가장 적합한 동영상 선택
        video_file = max(
            [vf for vf in videos[0]['video_files'] if vf['width'] == 640],
            key=lambda x: x.get('height', 0)
        )
        video_url = video_file['link']
        
        path = Config.TEMP_DIR / f"pexels_{uuid.uuid4()}.mp4"
        
        with requests.get(video_url, stream=True) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        logger.info(f"🎥 Pexels 동영상 다운로드 완료: {path}")
        return str(path)
    except Exception as e:
        logger.warning(f"[Pexels 실패] {e}, 기본 배경 생성")
        return create_simple_video(duration)

# ✅ 개선된 단색 배경 영상 생성 (ImageMagick 없이)
def create_simple_video(duration=60) -> str:
    colors = [
        (30, 144, 255),  # 도더블루
        (255, 69, 0),    # 오렌지레드
        (46, 139, 87),   # 씨그린
        (147, 112, 219), # 미디움퍼플
        (220, 20, 60)    # 크림슨
    ]
    path = Config.TEMP_DIR / f"bg_{uuid.uuid4()}.mp4"
    color = random.choice(colors)
    
    # FFmpeg로 직접 생성 (ImageMagick 사용 안함)
    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'color=c={color[0]:02x}{color[1]:02x}{color[2]:02x}:s={Config.SHORTS_WIDTH}x{Config.SHORTS_HEIGHT}:d={duration}',
        '-pix_fmt', 'yuv420p',
        '-y', str(path)
    ]
    subprocess.run(cmd, check=True)
    
    return str(path)

# ✅ 텍스트 이미지 생성 (ImageMagick 대체)
def create_text_image(text: str, fontsize: int, color: str, bg_color=None):
    font = ImageFont.load_default()  # 기본 폰트 사용
    if bg_color is None:
        bg_color = (0, 0, 0, 0)  # 투명 배경
    
    # 텍스트 크기 계산
    dummy_img = Image.new('RGB', (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    text_width, text_height = dummy_draw.textsize(text, font=font)
    
    # 이미지 생성
    img = Image.new('RGBA', (text_width + 20, text_height + 20), bg_color)
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), text, fill=color, font=font)
    
    img_path = Config.TEMP_DIR / f"text_{uuid.uuid4()}.png"
    img.save(str(img_path))
    return str(img_path)

# ✅ 영상 합치기 (ImageMagick 없이)
def create_shorts_video(video_path: str, audio_path: str, title: str) -> str:
    try:
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)

        # 동영상 길이 조정
        if video.duration < audio.duration:
            video = video.loop(duration=audio.duration)
        else:
            video = video.subclip(0, audio.duration)

        # 제목 텍스트 이미지 생성
        title_img_path = create_text_image(title, 70, "white")
        title_clip = VideoFileClip(title_img_path).set_duration(audio.duration)
        title_clip = title_clip.set_position(('center', 'top'))

        # 해시태그 텍스트 이미지 생성
        hashtags = "#쇼츠 #유튜브 #자동생성"
        hashtag_img_path = create_text_image(hashtags, 40, "white")
        hashtag_clip = VideoFileClip(hashtag_img_path).set_duration(audio.duration)
        hashtag_clip = hashtag_clip.set_position(('center', 0.9), relative=True)

        # 영상 합성
        final = CompositeVideoClip([video, title_clip, hashtag_clip])
        final = final.set_audio(audio)
        
        output = Config.OUTPUT_DIR / f"shorts_{uuid.uuid4()}.mp4"
        
        # 안정적인 출력 설정
        final.write_videofile(
            str(output),
            fps=24,
            threads=4,
            preset='ultrafast',
            ffmpeg_params=['-crf', '28'],
            logger=None
        )
        
        logger.info(f"🎬 영상 생성 완료: {output}")
        return str(output)
    except Exception as e:
        logger.error(f"[영상 생성 실패] {e}")
        raise

# ✅ Gemini 콘텐츠 생성 (안정화 버전)
def generate_content_with_gemini(topic: str) -> dict:
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("Gemini API 키가 없어 기본 콘텐츠 사용")
            raise Exception("API 키 없음")

        genai.configure(api_key=api_key, transport='rest')
        model = genai.GenerativeModel('gemini-1.0-pro')  # 최신 모델 사용
        
        prompt = f"""
        한국어로 유튜브 쇼츠용 콘텐츠를 생성해주세요. 다음 형식으로 응답하세요:

        제목: {topic}에 대한 놀라운 사실
        스크립트: 안녕하세요! {topic}에 대해 알려드립니다. 첫 번째로...
        해시태그: #{topic} #비밀 #쇼츠
        """
        
        response = model.generate_content(prompt)
        
        # 기본 콘텐츠
        content = {
            "title": f"{topic}의 비밀",
            "script": f"{topic}에 대해 알려드리는 중요한 정보입니다!",
            "hashtags": [f"#{topic}", "#비밀", "#쇼츠"]
        }
        
        # 응답 처리
        if response.text:
            lines = response.text.split('\n')
            for line in lines:
                if line.startswith("제목:"):
                    content["title"] = line.split(":")[1].strip()
                elif line.startswith("스크립트:"):
                    content["script"] = line.split(":")[1].strip()
                elif line.startswith("해시태그:"):
                    content["hashtags"] = [tag.strip() for tag in line.split(":")[1].strip().split()]
        
        return content
    except Exception as e:
        logger.error(f"[Gemini 실패] {e}, 기본 콘텐츠 사용")
        return {
            "title": f"{topic}의 비밀",
            "script": f"{topic}에 대해 알려드리는 중요한 정보입니다!",
            "hashtags": [f"#{topic}", "#비밀", "#쇼츠"]
        }

# ✅ 임시 파일 정리
def cleanup_temp_files():
    for f in Config.TEMP_DIR.glob("*"):
        try:
            f.unlink()
        except:
            pass

# ✅ 메인 함수
def main():
    try:
        # ImageMagick 보안 정책 수정
        fix_imagemagick_policy()
        
        topic = "부자 되는 법"
        logger.info("🚀 유튜브 쇼츠 자동 생성 시작")
        
        # 1. 콘텐츠 생성
        content = generate_content_with_gemini(topic)
        logger.info(f"🎯 생성된 콘텐츠: {content}")
        
        # 2. 음성 생성
        audio_path = generate_tts(content["script"])
        
        # 3. 배경 영상 준비
        bg_video = get_background_video(topic, 60)
        logger.info(f"🖼️ 사용된 배경 영상: {bg_video}")
        
        # 4. 영상 생성
        final_path = create_shorts_video(bg_video, audio_path, content["title"])
        logger.info(f"🎉 최종 영상 저장 완료: {final_path}")
        
        # 5. 임시 파일 정리
        cleanup_temp_files()
        
        return final_path
    except Exception as e:
        logger.error(f"💥 심각한 오류 발생: {e}")
        raise

if __name__ == "__main__":
    main()
