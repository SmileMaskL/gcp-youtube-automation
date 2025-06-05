import os
import requests
import logging
import tempfile
from moviepy.editor import ImageClip, TextClip, concatenate_videoclips, CompositeVideoClip, AudioFileClip, ColorClip, CompositeAudioClip
from PIL import Image
from .utils import get_secret
import shutil

logger = logging.getLogger(__name__)

# API 키
PEXELS_API_KEY = get_secret("PEXELS_API_KEY")
ELEVENLABS_API_KEY = get_secret("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = "uyVNoMrnUku1dZyVEXwD"  # 안나 킴 음성

def download_file(url, path):
    """파일 다운로드 유틸리티"""
    response = requests.get(url, stream=True)
    with open(path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def download_pexels_image(query):
    """Pexels에서 이미지 다운로드"""
    try:
        url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
        headers = {"Authorization": PEXELS_API_KEY}
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        if data.get('photos'):
            image_url = data['photos'][0]['src']['large']
            temp_dir = tempfile.mkdtemp()
            img_path = os.path.join(temp_dir, "background.jpg")
            download_file(image_url, img_path)
            return img_path
    except Exception as e:
        logger.error(f"⚠️ Pexels 이미지 오류: {str(e)}")
    return None

def generate_audio_from_text(text, voice_id):
    """ElevenLabs 음성 생성"""
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, "voiceover.mp3")
        
        response = requests.post(url, json=data, headers=headers)
        with open(audio_path, 'wb') as f:
            f.write(response.content)
            
        return audio_path
        
    except Exception as e:
        logger.error(f"⚠️ 음성 생성 오류: {str(e)}")
        return None

def create_video(topic, script, title_text):
    """영상 생성 메인 함수 (배경 음악 추가)"""
    temp_files = []
    try:
        # 1. 배경 이미지
        image_path = download_pexels_image(topic)
        if image_path:
            temp_files.append(os.path.dirname(image_path))
            img = Image.open(image_path)
            img = img.resize((1920, 1080), Image.LANCZOS)
            img.save(image_path)
            bg_clip = ImageClip(image_path)
        else:
            bg_clip = ColorClip((1920, 1080), color=(0, 0, 0))
        
        # 2. 스크립트 분할 및 음성 생성
        sentences = [s.strip() for s in script.split('\n') if s.strip()]
        audio_clips = []
        text_clips = []
        current_time = 0
        
        for sentence in sentences:
            audio_path = generate_audio_from_text(sentence, ELEVENLABS_VOICE_ID)
            if audio_path:
                temp_files.append(os.path.dirname(audio_path))
                audio_clip = AudioFileClip(audio_path)
                audio_clips.append(audio_clip)
                
                # 텍스트 클립 생성
                txt_clip = TextClip(
                    sentence,
                    fontsize=70,
                    color='yellow',
                    font="fonts/Catfont.ttf",
                    stroke_color='black',
                    stroke_width=2,
                    size=(1800, None),
                    method='caption'
                ).set_position('center').set_duration(audio_clip.duration)
                
                text_clips.append(txt_clip.set_start(current_time))
                current_time += audio_clip.duration
        
        # 3. 배경 음악 추가
        bgm_path = None
        try:
            bgm_url = "https://cdn.pixabay.com/download/audio/2024/02/22/audio_1d0a0d6d1b.mp3"  # 무료 음원
            bgm_path = "background_music.mp3"
            if not os.path.exists(bgm_path):
                download_file(bgm_url, bgm_path)
                
            bgm = AudioFileClip(bgm_path).volumex(0.2)
            if current_time > 0:
                bgm = bgm.set_duration(current_time)
        except Exception as e:
            logger.warning(f"⚠️ 배경 음악 오류: {str(e)}")
            bgm = None
        
        # 4. 비디오 조립
        final_audio = concatenate_audioclips(audio_clips)
        if bgm:
            final_audio = CompositeAudioClip([final_audio, bgm])
        
        video_duration = max(current_time, 10)
        bg_clip = bg_clip.set_duration(video_duration)
        final_video = CompositeVideoClip([bg_clip] + text_clips, size=(1920, 1080)).set_audio(final_audio)
        
        # 5. 영상 저장
        os.makedirs("output", exist_ok=True)
        output_path = os.path.join("output", f"{topic.replace(' ', '_')}_{int(time.time())}.mp4")
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='fast'
        )
        
        return output_path
        
    except Exception as e:
        logger.error(f"❌ 영상 생성 실패: {str(e)}")
        return None
        
    finally:
        # 임시 파일 정리
        for path in temp_files:
            if os.path.exists(path):
                shutil.rmtree(path)
