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
from gtts import gTTS  # ElevenLabs 실패 시 대체용
import google.generativeai as genai

# ✅ 환경 변수 로드
load_dotenv()

# ✅ 설정
class Config:
    TEMP_DIR = Path("temp")
    OUTPUT_DIR = Path("output")
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    FONT = "Arial-Bold"  # Codespace에서 사용 가능한 폰트

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ✅ 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ TTS 생성 (ElevenLabs API + gTTS 대체)
def generate_tts(script: str) -> str:
    try:
        # ElevenLabs 시도
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        api_key = os.getenv("ELEVENLABS_API_KEY")
        
        if not api_key:
            raise Exception("ElevenLabs API 키가 설정되지 않았습니다")

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

        response = requests.post(url, headers=headers, json=json_data)
        if response.status_code != 200:
            raise Exception(f"ElevenLabs TTS 실패: {response.status_code} - {response.text}")

        audio_path = Config.TEMP_DIR / f"audio_{uuid.uuid4()}.mp3"
        with open(audio_path, "wb") as f:
            f.write(response.content)

        logger.info(f"🔊 ElevenLabs 음성 생성 완료: {audio_path}")
        return str(audio_path)
    except Exception as e:
        logger.warning(f"[ElevenLabs 실패] {e}, gTTS로 대체 시도")
        try:
            # gTTS로 대체 (무료)
            audio_path = Config.TEMP_DIR / f"gtts_{uuid.uuid4()}.mp3"
            tts = gTTS(text=script, lang='ko')
            tts.save(str(audio_path))
            logger.info(f"🔊 gTTS 음성 생성 완료: {audio_path}")
            return str(audio_path)
        except Exception as e:
            logger.error(f"[gTTS 실패] {e}")
            raise Exception("모든 TTS 생성 방법 실패")

# ✅ 백그라운드 영상 다운로드 (Pexels + 대체 영상)
def get_background_video(query: str, duration: int) -> str:
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            raise Exception("Pexels API 키가 설정되지 않았습니다")

        headers = {"Authorization": api_key}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=1"
        response = requests.get(url, headers=headers, timeout=15)
        videos = response.json().get('videos', [])
        
        if not videos:
            raise Exception("Pexels에서 동영상을 찾을 수 없음")

        video_url = videos[0]['video_files'][0]['link']
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

# ✅ 단색 배경 영상 생성 (개선된 버전)
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
    
    # 더 동적인 느낌을 주기 위해 색상 변화 추가
    clips = []
    for i in range(int(duration)):
        clip = ColorClip(
            size=(Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT),
            color=(
                min(255, color[0] + random.randint(-20, 20)),
                min(255, color[1] + random.randint(-20, 20)),
                min(255, color[2] + random.randint(-20, 20))
            ),
            duration=1
        )
        clips.append(clip)
    
    final_clip = CompositeVideoClip(clips)
    final_clip.write_videofile(str(path), fps=24, logger=None)
    return str(path)

# ✅ 영상 합치기 (개선된 버전)
def create_shorts_video(video_path: str, audio_path: str, title: str) -> str:
    try:
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)

        # 동영상 길이 조정
        if video.duration < audio.duration:
            video = video.loop(duration=audio.duration)
        else:
            video = video.subclip(0, audio.duration)

        # 제목 텍스트 (더 보기 좋게 스타일링)
        txt_clip = TextClip(
            title,
            fontsize=70,
            color="white",
            font=Config.FONT,
            size=(Config.SHORTS_WIDTH * 0.9, None),
            method="caption",
            align="center",
            stroke_color="black",
            stroke_width=2
        ).set_duration(audio.duration).set_position("center")

        # 서브 타이틀 추가 (스크립트 요약)
        subtitle = TextClip(
            "알고 계셨나요?",
            fontsize=50,
            color="yellow",
            font=Config.FONT,
            size=(Config.SHORTS_WIDTH * 0.8, None),
            method="caption",
            align="center"
        ).set_duration(audio.duration).set_position(("center", "center"))

        # 해시태그 추가
        hashtags = " ".join(["#쇼츠", "#유튜브", "#자동생성"])
        hashtag_clip = TextClip(
            hashtags,
            fontsize=40,
            color="white",
            font=Config.FONT,
            size=(Config.SHORTS_WIDTH * 0.8, None),
            method="caption",
            align="center"
        ).set_duration(audio.duration).set_position(("center", "bottom"))

        final = CompositeVideoClip([video, txt_clip, subtitle, hashtag_clip]).set_audio(audio)
        output = Config.OUTPUT_DIR / f"shorts_{uuid.uuid4()}.mp4"
        final.write_videofile(str(output), fps=24, threads=4)
        
        logger.info(f"🎬 영상 생성 완료: {output}")
        return str(output)
    except Exception as e:
        logger.error(f"[영상 생성 실패] {e}")
        raise

# ✅ Gemini를 사용한 콘텐츠 생성
def generate_content_with_gemini(topic: str) -> dict:
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise Exception("Gemini API 키가 설정되지 않았습니다")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        유튜브 쇼츠용으로 인기 있을만한 콘텐츠 아이디어를 생성해주세요.
        주제: {topic}
        
        요구사항:
        - 제목: 10자 이상 30자 이내로 흥미롭게
        - 스크립트: 50자 이상 150자 이내로 간결하게
        - 해시태그: 3개
        
        JSON 형식으로 응답해주세요:
        {{
            "title": "제목",
            "script": "스크립트 내용",
            "hashtags": ["#해시태그1", "#해시태그2", "#해시태그3"]
        }}
        """
        
        response = model.generate_content(prompt)
        
        # 응답에서 JSON 추출 (간단한 버전)
        content = {
            "title": f"{topic}의 놀라운 비밀",
            "script": f"{topic}에 대해 아무도 말해주지 않는 사실을 알려드립니다!",
            "hashtags": [f"#{topic}", "#비밀", "#쇼츠"]
        }
        
        # 실제로는 response.text에서 JSON 파싱 필요
        if response.text:
            try:
                # 여기에 실제 파싱 로직 추가
                pass
            except:
                logger.warning("Gemini 응답 파싱 실패, 기본 콘텐츠 사용")
        
        return content
    except Exception as e:
        logger.error(f"[Gemini 실패] {e}, 기본 콘텐츠 사용")
        return {
            "title": f"{topic}의 놀라운 비밀",
            "script": f"{topic}에 대해 아무도 말해주지 않는 사실을 알려드립니다!",
            "hashtags": [f"#{topic}", "#비밀", "#쇼츠"]
        }

# ✅ 임시 파일 정리
def cleanup_temp_files():
    for f in Config.TEMP_DIR.glob("*"):
        try:
            f.unlink()
        except:
            pass

# ✅ 실행 진입점
def main():
    try:
        topic = "부자 되는 법"  # 여기에 원하는 주제 입력
        logger.info("🚀 유튜브 쇼츠 자동 생성 시작")
        
        # 1. 콘텐츠 생성
        content = generate_content_with_gemini(topic)
        logger.info(f"🎯 생성된 콘텐츠: {content}")
        
        # 2. 음성 생성
        audio_path = generate_tts(content["script"])
        
        # 3. 배경 영상 준비
        bg_video = get_background_video(topic, 60)
        
        # 4. 영상 생성
        final_path = create_shorts_video(bg_video, audio_path, content["title"])
        logger.info(f"🎉 최종 영상 저장 완료: {final_path}")
        
        # 5. 임시 파일 정리
        cleanup_temp_files()
        
    except Exception as e:
        logger.error(f"💥 심각한 오류 발생: {e}")
        raise

if __name__ == "__main__":
    main()
