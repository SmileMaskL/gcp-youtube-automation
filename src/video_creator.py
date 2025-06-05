import os
import requests
import logging
import tempfile
from moviepy.editor import ImageClip, TextClip, concatenate_videoclips, CompositeVideoClip, AudioFileClip, ColorClip
from PIL import Image, ImageDraw, ImageFont # PIL 임포트 유지 (폰트 확인 및 기타 용도)
from .utils import get_secret
import shutil # tempfile로 생성된 디렉토리 삭제 위함

logger = logging.getLogger(__name__)

# Pexels API 키 동적 로드
PEXELS_API_KEY = get_secret("PEXELS_API_KEY")
ELEVENLABS_API_KEY = get_secret("ELEVENLABS_API_KEY") # ElevenLabs API 키 로드
ELEVENLABS_VOICE_ID = "uyVNoMrnUku1dZyVEXwD" # 안나 킴 음성 ID

def download_pexels_image(query):
    """저작권 없는 고품질 이미지 다운로드 (Pexels API)"""
    try:
        url = f"https://api.pexels.com/v1/search?query={query}&orientation=landscape&per_page=1" # 가로 방향 이미지 선호
        headers = {"Authorization": PEXELS_API_KEY}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        data = response.json()
        
        if 'photos' in data and data['photos']:
            image_url = data['photos'][0]['src']['large'] # large 사이즈
            img_data = requests.get(image_url, timeout=15).content
            
            temp_dir = tempfile.mkdtemp(prefix="pexels_img_")
            img_path = os.path.join(temp_dir, f"{query.replace(' ', '_')}.jpg")
            with open(img_path, 'wb') as f:
                f.write(img_data)
            logger.info(f"Pexels 이미지 다운로드 완료: {img_path}")
            return img_path
        else:
            logger.warning(f"Pexels에서 '{query}'에 대한 이미지를 찾을 수 없습니다. 기본 이미지 사용.")
            return None # 이미지를 찾지 못하면 None 반환
    except requests.exceptions.RequestException as req_e:
        logger.error(f"Pexels 이미지 다운로드 요청 실패: {req_e}")
        return None
    except Exception as e:
        logger.error(f"Pexels 이미지 다운로드 실패: {str(e)}\n{traceback.format_exc()}")
        return None

def generate_audio_from_text(text, voice_id):
    """ElevenLabs API를 사용하여 텍스트를 음성으로 변환"""
    if not ELEVENLABS_API_KEY:
        logger.error("ELEVENLABS_API_KEY가 설정되지 않았습니다.")
        raise ValueError("ELEVENLABS_API_KEY 환경 변수 미설정")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2", # 다국어 모델
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    temp_audio_file = None
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        temp_dir = tempfile.mkdtemp(prefix="elevenlabs_audio_")
        temp_audio_file = os.path.join(temp_dir, "generated_audio.mp3")
        with open(temp_audio_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        logger.info(f"ElevenLabs 음성 생성 완료: {temp_audio_file}")
        return temp_audio_file
    except requests.exceptions.RequestException as req_e:
        logger.error(f"ElevenLabs 음성 생성 요청 실패: {req_e}")
        raise
    except Exception as e:
        logger.error(f"ElevenLabs 음성 생성 실패: {str(e)}\n{traceback.format_exc()}")
        if temp_audio_file and os.path.exists(temp_audio_file):
            os.remove(temp_audio_file) # 실패 시 임시 파일 삭제
        raise

def create_video(topic, script, title_text_for_thumbnail):
    """
    동영상 생성 (스크립트 길이에 따라 유연하게, 최소 10초)
    주어진 스크립트를 기반으로 음성을 생성하고, Pexels 이미지와 텍스트를 합성합니다.
    """
    temp_files_to_clean = [] # 생성된 임시 파일 목록 (마지막에 삭제)

    try:
        # 1. Pexels에서 배경 이미지 다운로드
        image_path = download_pexels_image(topic)
        if not image_path:
            # 이미지를 찾지 못하면 대체 이미지 사용 또는 검정 배경으로 진행
            logger.warning("Pexels 이미지를 찾을 수 없어 검정 배경으로 진행합니다.")
            bg_clip = ColorClip((1920, 1080), color=(0,0,0)).set_duration(10) # 10초 기본 검정 배경
            image_clip_base = bg_clip # 기본 배경 클립 설정
        else:
            temp_files_to_clean.append(os.path.dirname(image_path)) # Pexels 이미지 임시 디렉토리 추가
            img = Image.open(image_path)
            # 이미지 리사이징 (풀 HD 1920x1080 비율로 조정)
            img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
            temp_resized_img_path = os.path.join(os.path.dirname(image_path), "resized_bg.jpg")
            img.save(temp_resized_img_path)
            image_clip_base = ImageClip(temp_resized_img_path)

        # 2. 스크립트를 문장 단위로 분할 및 음성 생성
        sentences = [s.strip() for s in script.replace('.', '.\n').replace('?', '?\n').replace('!', '!\n').split('\n') if s.strip()]
        
        audio_clips = []
        text_clips = []
        total_audio_duration = 0
        
        # 폰트 로드 (고양이체.ttf)
        font_path = "fonts/Catfont.ttf"
        try:
            font = ImageFont.truetype(font_path, 60) # 영상 내 자막용 폰트
        except IOError:
            logger.warning(f"⚠️ 폰트 '{font_path}'를 찾을 수 없습니다. 기본 폰트 또는 Noto Sans CJK KR을 시도합니다.")
            try:
                font = ImageFont.truetype("NotoSansKR-Regular.ttf", 60) # Linux 환경 경로
            except IOError:
                logger.warning("⚠️ NotoSansKR-Regular.ttf 폰트도 찾을 수 없습니다. 기본 Arial 폰트 사용.")
                font = ImageFont.truetype("arial.ttf", 60)

        for i, sentence in enumerate(sentences):
            if not sentence: continue # 빈 문장 건너뛰기
            try:
                audio_file = generate_audio_from_text(sentence, ELEVENLABS_VOICE_ID)
                temp_files_to_clean.append(os.path.dirname(audio_file)) # ElevenLabs 오디오 임시 디렉토리 추가
                audio_clip = AudioFileClip(audio_file)
                audio_clips.append(audio_clip)
                
                # 각 문장에 맞는 텍스트 클립 생성
                txt_clip = TextClip(
                    sentence,
                    fontsize=60,
                    color='yellow',
                    font=font_path if os.path.exists(font_path) else 'NotoSansKR-Regular', # 폰트 경로 또는 이름
                    stroke_color='black',
                    stroke_width=2,
                    method='caption', # 텍스트가 길 경우 자동 줄 바꿈
                    size=(1800, None) # 가로 최대 1800px, 세로는 자동 조절
                ).set_position('center').set_duration(audio_clip.duration)
                text_clips.append(txt_clip.set_start(total_audio_duration)) # 시작 시간 설정
                
                total_audio_duration += audio_clip.duration
            except Exception as e:
                logger.error(f"음성/텍스트 클립 생성 실패 (문장: '{sentence}'): {e}")
                # 실패 시 해당 문장은 건너뛰고 다음 문장으로 진행
                continue

        if not audio_clips:
            logger.error("생성된 오디오 클립이 없습니다. 영상 제작 불가.")
            raise ValueError("No audio clips generated, video creation failed.")

        final_audio = concatenate_audioclips(audio_clips)
        final_video_duration = max(total_audio_duration, 10) # 최소 10초 유지

        # 배경 영상 클립 생성 (총 오디오 길이에 맞추거나 최소 10초)
        background_clip = image_clip_base.set_duration(final_video_duration).resize(image_clip_base.size)
        
        # 모든 클립 합성
        video_clips = [background_clip] + text_clips
        final_clip = CompositeVideoClip(video_clips, size=(1920, 1080)) # 최종 영상 크기
        final_clip = final_clip.set_audio(final_audio)

        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        # 파일명에 타임스탬프 추가하여 중복 방지
        output_path = os.path.join(output_dir, f"{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4")
        
        # 저사양 PC를 위한 최적화 설정
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            threads=2, # CPU 코어 수 고려하여 조정 (2~4 권장)
            preset='medium', # 'medium' 또는 'fast'
            logger=None # MoviePy 자체 로깅 비활성화 (Flask 로거 사용)
        )
        logger.info(f"🎬 영상 생성 완료: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"🔴 영상 생성 실패: {str(e)}\n{traceback.format_exc()}")
        raise # 영상 생성 실패 시 예외 발생
    finally:
        # 임시 파일 및 디렉토리 정리
        for temp_path in temp_files_to_clean:
            if os.path.exists(temp_path):
                try:
                    shutil.rmtree(temp_path) # 폴더째 삭제
                    logger.info(f"🗑️ 임시 디렉토리 삭제: {temp_path}")
                except Exception as e:
                    logger.warning(f"⚠️ 임시 디렉토리 삭제 실패 ({temp_path}): {e}")
        if 'temp_resized_img_path' in locals() and os.path.exists(temp_resized_img_path):
            os.remove(temp_resized_img_path)
            logger.info(f"🗑️ 리사이징된 이미지 파일 삭제: {temp_resized_img_path}")
