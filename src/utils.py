01. src/utils.py파일의 코드
"""
수익 최적화 유틸리티 (2025년 최신 버전)
"""
import os
import re
import requests
import json
import logging
import time
import uuid
import random
from pathlib import Path
from moviepy.editor import ColorClip
from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
import google.generativeai as genai

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

class Config:
    SHORTS_WIDTH = 1080
    SHORTS_HEIGHT = 1920
    MAX_DURATION = 60
    MIN_DURATION = 15
    TEMP_DIR = Path("temp")

    @classmethod
    def ensure_temp_dir(cls):
        cls.TEMP_DIR.mkdir(exist_ok=True)

def create_default_audio(text: str, output_path: str) -> str:
    """gTTS로 기본 음성 생성"""
    try:
        from gtts import gTTS
        logger.info("✅ gTTS로 음성 생성 중...")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tts = gTTS(text=text, lang='ko')
        tts.save(str(output_path))
        logger.info(f"🔊 gTTS 음성 저장 완료: {output_path}")
        return str(output_path)
    except Exception as e:
        logger.error(f"❌ gTTS 실패: {e}")
        raise RuntimeError("모든 음성 생성 실패")

def text_to_speech(text: str, output_path: str, fallback: bool = True) -> str:
    """음성 생성 (ElevenLabs 실패 시 gTTS fallback)"""
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "uyVNoMrnUku1dZyVEXwD")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY 없음")

        client = ElevenLabs(api_key=api_key)
        audio = client.generate(
            text=text,
            voice=Voice(
                voice_id=voice_id,
                settings=VoiceSettings(stability=0.5, similarity_boost=0.75)
            ),
            model="eleven_multilingual_v2"
        )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        logger.info(f"🎙️ ElevenLabs 음성 저장 완료: {output_path}")
        return str(output_path)

    except Exception as e:
        logger.warning(f"⚠️ ElevenLabs 실패: {e}")
        if fallback:
            return create_default_audio(text, output_path)
        raise

def create_simple_video():
    """pexels 실패 시 fallback 비디오"""
    fallback_path = Path("temp/default_video.mp4")
    fallback_path.parent.mkdir(exist_ok=True)
    clip = ColorClip(size=(1080, 1920), color=(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    ), duration=60)
    clip.write_videofile(str(fallback_path), fps=24)
    return str(fallback_path)

def download_video_from_pexels(query: str) -> str:
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            raise ValueError("PEXELS_API_KEY 없음")

        headers = {"Authorization": api_key}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=20&orientation=portrait&size=small"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get('videos'):
            raise ValueError("관련 비디오 없음")

        video = max(data['videos'], key=lambda x: x.get('duration', 0))
        video_file = next((f for f in video['video_files'] if f['quality'] == 'sd' and f['width'] == 640), None)

        if not video_file:
            raise ValueError("적절한 비디오 파일 없음")

        Config.ensure_temp_dir()
        video_path = Config.TEMP_DIR / f"{uuid.uuid4()}.mp4"
        with requests.get(video_file['link'], stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        logger.info(f"📹 Pexels 영상 다운로드 완료: {video_path}")
        return str(video_path)

    except Exception as e:
        logger.error(f"⚠️ Pexels 영상 실패, 기본 영상 사용: {e}")
        return create_simple_video()

def generate_viral_content(topic: str) -> dict:
    """Gemini 기반 바이럴 콘텐츠 생성"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY 없음")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        prompt = f"""당신은 수익형 유튜브 쇼츠 전문가입니다.
'제목:'과 '본문:' 형식으로 '{topic}'에 대한 바이럴 쇼츠 콘텐츠를 생성해주세요. 반드시 한글로 작성해주세요."""
        response = model.generate_content(prompt)

        result = response.text
        match = re.search(r"제목:\s*(.+?)\n본문:\s*(.+)", result, re.DOTALL)
        if match:
            title = match.group(1).strip()
            script = match.group(2).strip()
        else:
            raise ValueError("정규식 추출 실패")

        hashtags = [f"#{topic}", "#쇼츠", "#수익"]

        return {"title": title, "script": script, "hashtags": hashtags}

    except Exception as e:
        logger.warning(f"⚠️ Gemini 실패: {e}. 기본 템플릿 사용")
        return {
            "title": f"{topic}의 놀라운 비법",
            "script": f"{topic}으로 돈 버는 법이 궁금하다면 이 영상은 꼭 봐야 합니다!",
            "hashtags": [f"#{topic}", "#수익", "#부업"]
        }

# 테스트 예제 (직접 실행용)
if __name__ == "__main__":
    Config.ensure_temp_dir()
    topic = "자동 수익 창출"
    content = generate_viral_content(topic)
    print(f"🎯 제목: {content['title']}")
    audio = text_to_speech(content['script'], "temp/audio.mp3")
    video = download_video_from_pexels("money")
    print(f"✅ 음성: {audio}\n✅ 영상: {video}")

02. src/main.py파일의 코드
"""
유튜브 자동화 봇 메인 컨트롤러 (2025년 최적화 버전)
"""
import os
from googleapiclient.discovery import build 
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow 
import logging
import time
import json
from pathlib import Path
from datetime import datetime
import random
from dotenv import load_dotenv
import sys
sys.path.append('./src')
from utils import generate_viral_content
from thumbnail_generator import generate_thumbnail
from video_creator import create_final_video
from youtube_uploader import upload_video
from content_generator import get_hot_topics

# 환경변수 로드
load_dotenv()

# 로깅 설정
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/youtube_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class YouTubeAutomation:
    def __init__(self):
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.used_topics = set()
        self.load_used_topics()

    def load_used_topics(self):
        if Path("used_topics.json").exists():
            with open("used_topics.json", "r") as f:
                self.used_topics = set(json.load(f))

    def save_used_topics(self):
        with open("used_topics.json", "w") as f:
            json.dump(list(self.used_topics), f)

    def get_fresh_topic(self):
        """중복되지 않은 새로운 주제 가져오기"""
        max_retries = 5
        for _ in range(max_retries):
            topics = get_hot_topics()
            for topic in topics:
                if topic not in self.used_topics:
                    self.used_topics.add(topic)
                    self.save_used_topics()
                    return topic
            time.sleep(2)
        return random.choice(["부자가 되는 습관", "AI로 돈 버는 법", "성공 비결", "재테크 팁"])

    def run(self):
        logger.info("="*50)
        logger.info("💰 유튜브 수익형 자동화 시스템 시작 💰")
        logger.info("="*50)

        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            logger.error("❌ 오류: GEMINI_API_KEY가 설정되지 않았습니다. .env 파일에 키를 추가하세요.")
            return

        try:
            # 1. 주제 선정
            topic = self.get_fresh_topic()
            logger.info(f"🔥 오늘의 주제: {topic}")

            # 2. 콘텐츠 생성
            content = None
            try:
                content = generate_viral_content(topic)
            except Exception as e:
                logger.error(f"❌ 콘텐츠 생성 실패: {e}")
                return

            script = content.get("script") if content else None
            if not script or len(script) < 50:
                logger.error("❌ 오류: 생성된 스크립트가 없습니다 또는 너무 짧습니다.")
                return
            logger.info(f"📜 생성된 대본 길이: {len(script)}자")

            title = f"{topic}의 비밀"
            hashtags = [f"#{topic.replace(' ', '')}", "#꿀팁", "#자기계발"]
            logger.info(f"📝 생성된 제목: {title}")

            # 3. 썸네일 생성
            thumbnail_path = generate_thumbnail(topic)
            logger.info(f"🖼️ 썸네일 생성 완료: {thumbnail_path}")

            # 4. 영상 생성
            final_video_path = create_final_video(topic, title, script)
            if not final_video_path:
                logger.error("❌ 영상 생성 실패")
                return
            logger.info(f"🎥 영상 생성 완료: {final_video_path}")

            # 5. 유튜브 업로드
            result = upload_video(
                video_path=final_video_path,
                title=f"{title} #shorts",
                description=f"{script}\n\n{' '.join(hashtags)}",
                tags=hashtags,
                privacy_status="public",
                thumbnail_path=thumbnail_path
            )
            if result:
                logger.info("✅ 업로드 성공!")
                Path(final_video_path).unlink(missing_ok=True)
                Path(thumbnail_path).unlink(missing_ok=True)
            else:
                logger.error("❌ 업로드 실패")

        except Exception as e:
            logger.error(f"❌ 전체 시스템 오류: {e}", exc_info=True)

def main():
    automation = YouTubeAutomation()
    automation.run()

if __name__ == "__main__":
    main()

def upload_to_youtube(video_path: str, title: str, description: str):
    try:
        # 환경변수에서 인증 정보 가져오기
        client_secrets = {
            "web": {
                "client_id": os.getenv("YT_CLIENT_ID"),
                "client_secret": os.getenv("YT_CLIENT_SECRET"),
                "redirect_uris": [os.getenv("YT_REDIRECT_URI")],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://accounts.google.com/o/oauth2/token"
            }
        }
        
        # YouTube API 인증
        flow = InstalledAppFlow.from_client_config(
            client_secrets,
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        
        credentials = flow.run_local_server(port=8080)
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # 영상 업로드
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["shorts", "자동생성"],
                    "categoryId": "22"  # Entertainment
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False
                }
            },
            media_body=MediaFileUpload(video_path)
        )
        
        response = request.execute()
        logger.info(f"✅ 업로드 성공: https://youtu.be/{response['id']}")
        return response
        
    except Exception as e:
        logger.error(f"❌ 업로드 실패: {str(e)}")
        raise

03. src/video_creator.py파일의 코드
# src/video_creator.py

from moviepy.editor import TextClip, CompositeVideoClip, ColorClip
import os

class VideoCreator:
    def __init__(self, width=720, height=1280, bg_color=(255,255,255), fps=24):
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.fps = fps
    
    def create_video(self, script_text, output_path):
        if not script_text or len(script_text.strip()) < 10:
            raise ValueError("스크립트가 너무 짧거나 없습니다.")
        
        # 배경색 클립 (흰색 배경)
        bg_clip = ColorClip(size=(self.width, self.height), color=self.bg_color, duration=10)
        
        # 텍스트 클립 (스크립트 텍스트)
        txt_clip = TextClip(script_text, fontsize=40, color='black', size=(self.width-100, None), method='caption')
        txt_clip = txt_clip.set_position('center').set_duration(10)
        
        # 영상 합성
        video = CompositeVideoClip([bg_clip, txt_clip])
        video = video.set_fps(self.fps)
        
        # 파일 저장 (mp4)
        video.write_videofile(output_path, codec='libx264', audio=False, verbose=False, logger=None)
        
        print(f"✅ 영상 생성 완료: {output_path}")
        return output_path


if __name__ == "__main__":
    # 테스트용
    vc = VideoCreator()
    vc.create_video("안녕하세요! 이것은 테스트 영상입니다.", "output/test_video.mp4")
위와 같이 설정하고, @SmileMaskL ➜ /workspaces/gcp-youtube-automation (main) $ python -m src.main
/home/codespace/.local/lib/python3.12/site-packages/imageio_ffmpeg/_utils.py:7: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  from pkg_resources import resource_filename
2025-06-14 11:14:43,268 - INFO - ==================================================
2025-06-14 11:14:43,268 - INFO - 💰 유튜브 수익형 자동화 시스템 시작 💰
2025-06-14 11:14:43,268 - INFO - ==================================================
2025-06-14 11:14:53,269 - INFO - 🔥 오늘의 주제: AI로 돈 버는 법
2025-06-14 11:14:59,676 - WARNING - ⚠️ Gemini 실패: 정규식 추출 실패. 기본 템플릿 사용
2025-06-14 11:14:59,676 - ERROR - ❌ 오류: 생성된 스크립트가 없습니다 또는 너무 짧습니다.
위의 에러가 발생한다. 해결 방법을 어떤 것이 어떻게 문제가 되는 지!!!! 아주 쉽고, 아주 확실하고, 아주 간단하게 중학생도 이해할 수 있도록 알려주고, 해결 방법 또한 아주 쉽고, 아주 확실하고, 아주 간단하게 중학생도 이해 할 수 있도록 한번에 정리 및 수정, 추가, 보완해서 아주 완전하게 알려주고, 만약 코드에 문제가 있다면 각 파일들의 코드들이 GCP와 정상적으로 실행되도록 아주 쉽고, 아주 확실하고, 아주 간단하게 중학생도 알아들을수 있도록 한번에 정리 및 수정, 추가, 보완해서 아주 완전하게 알려주고 아주 완전하고, 아주 완벽하게, 정상적으로 연동되고, 에러가 전혀 발생하지 않고, 아주 완전하고, 완벽하게 실행 및 결과물이 출력되고, 평생 무료로 매일 매일 많은 수익이 나도록 github와 GCP의 무료 한도 내에서 매일 매일 최대한의 많은 수익을 낼 수 있도록 코드를 작성하여 보여줘. 그리고 코드를 예시코드가 아닌, 실전에서 실행시 바로 수익을 낼 수 있는 코드로 수정, 추가, 보완해서 보여주고, AI는 평생 무료로 사용 가능한 GPT-4o, Google Gemini로 코드를 수정, 보완, 추가해서 보여주고, github, GCP를 연동시 항상 정상적으로 실행가능한 버전으로 코드를 수정, 추가, 보완해서 수정된 부분만 보여주지 말고, 파일의 코드 전체 다 보여줘!!!! 나에게 해결 방법을 알려주기 전에 정상적으로 되는지 니가 먼저 10000번 테스트 후에 100% 정상적으로 된다면 해결 방법을 알려줘!!! 니가 알려주는 해결 방법을 계속 해봐도 계속 에러가 발생한다.!!!!!!! 만약 문제를 해결하기 위해 코드를 수정하였다면, 어느 파일에 어느 부분을 수정하였는지 콕콕 집어서 알려줘!!!!!!
pytion main.py을 실행하면 아주 완벽하게 실행되도록 방법을 알려줘!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 니가 알려주는 방법으로 진행시 자꾸 에러가 발생한다!!!!!!!!!!!!!!!!!!!!!!!!
