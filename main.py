import os
import random
import time
from datetime import datetime
import logging
import textwrap
import subprocess
import requests

from PIL import Image, ImageDraw, ImageFont
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import openai
import google.generativeai as genai
from pexels_api import API

# --- 로깅 설정 ---
# Cloud Run Job의 로그를 표준 출력으로 바로 확인하기 위해 StreamHandler만 사용합니다.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class YouTubeAutomationJob:
    def __init__(self):
        """환경 변수에서 모든 설정을 로드하고 클래스를 초기화합니다."""
        logger.info("🚀 유튜브 자동화 작업을 시작합니다.")
        # --- API 키 로드 ---
        self.openai_keys = os.getenv('OPENAI_API_KEYS', '').split(',')
        self.pexels_key = os.getenv('PEXELS_API_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.youtube_creds_info = {
            'client_id': os.getenv('YOUTUBE_CLIENT_ID'),
            'client_secret': os.getenv('YOUTUBE_CLIENT_SECRET'),
            'refresh_token': os.getenv('YOUTUBE_REFRESH_TOKEN'),
            'token_uri': 'https://oauth2.googleapis.com/token',
            'scopes': ['https://www.googleapis.com/auth/youtube.upload']
        }
        
        # --- 필수 키 검증 ---
        if not all([self.openai_keys, self.pexels_key, self.gemini_key, 
                    self.youtube_creds_info['client_id'], self.youtube_creds_info['client_secret'], 
                    self.youtube_creds_info['refresh_token']]):
            logger.critical("❌ 치명적 오류: 필수 API 키 또는 인증 정보가 환경 변수에 없습니다.")
            raise ValueError("필수 환경 변수가 설정되지 않았습니다.")

        # --- 서비스 클라이언트 설정 ---
        self.current_openai_key = random.choice(self.openai_keys)
        openai.api_key = self.current_openai_key
        genai.configure(api_key=self.gemini_key)
        self.gemini = genai.GenerativeModel('gemini-pro')
        self.pexels = API(self.pexels_key)
        self.youtube = self._setup_youtube()
        logger.info("✅ 모든 서비스 클라이언트가 성공적으로 초기화되었습니다.")

    def _setup_youtube(self):
        """유튜브 API 클라이언트를 설정합니다."""
        creds = Credentials.from_authorized_user_info(self.youtube_creds_info)
        return build('youtube', 'v3', credentials=creds)

    def _rotate_openai_key(self):
        """OpenAI API 키를 교체합니다."""
        self.current_openai_key = random.choice(self.openai_keys)
        openai.api_key = self.current_openai_key
        logger.info(f"🔄 OpenAI 키를 교체했습니다: ...{self.current_openai_key[-4:]}")

    def _generate_script(self, topic):
        """Gemini 또는 GPT-4o를 사용하여 영상 스크립트를 생성합니다."""
        logger.info(f"✍️ 주제 '{topic}'에 대한 스크립트 생성을 시작합니다.")
        prompt = (f"60초 분량의 유튜브 쇼츠 동영상 스크립트를 작성해 줘.\n"
                  f"주제: {topic}\n"
                  f"구조: 1. 시선을 사로잡는 강력한 오프닝 (5초). 2. 핵심 정보 3가지. 3. 구독과 좋아요를 유도하는 마무리.\n"
                  f"스타일: 간결하고, 긍정적이며, 유익한 톤.\n"
                  f"필수 포함 해시태그: #shorts #꿀팁 #{topic.replace(' ', '')}")
        try:
            # 70% 확률로 비용 효율적인 Gemini 사용
            if random.random() < 0.7:
                logger.info("🤖 Gemini API를 사용하여 생성합니다.")
                response = self.gemini.generate_content(prompt)
                return response.text
            else:
                logger.info("🤖 GPT-4o API를 사용하여 생성합니다.")
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8, max_tokens=600
                )
                return response.choices[0].message['content']
        except Exception as e:
            logger.error(f"스크립트 생성 중 오류 발생: {e}")
            self._rotate_openai_key()
            logger.info("API 키 교체 후 재생성을 시도합니다.")
            return self.gemini.generate_content(prompt).text # 실패 시 Gemini로 재시도

    def _optimize_title(self, topic):
        """생성된 주제를 기반으로 클릭을 유도하는 제목을 생성합니다."""
        logger.info("📝 영상 제목 최적화를 시작합니다.")
        try:
            response = self.gemini.generate_content(
                f"'{topic}'을 주제로 한 유튜브 쇼츠 영상의 제목을 5개 제안해 줘. "
                "조건: 1. 이모지 2개 이상 사용. 2. 숫자나 놀라운 사실 포함. 3. 50자 이내."
            )
            # 제안된 제목 중 하나를 무작위로 선택
            optimized_titles = [line.strip() for line in response.text.split('\n') if line.strip()]
            return random.choice(optimized_titles)
        except Exception as e:
            logger.error(f"제목 최적화 실패: {e}")
            return f"{topic}에 대한 믿을 수 없는 사실! 🤯"

    def _create_video_and_thumbnail(self, title, script):
        """Pexels에서 배경 이미지를 받고, 썸네일과 최종 영상을 제작합니다."""
        logger.info("🎨 썸네일 및 영상 제작을 시작합니다.")
        try:
            # 1. Pexels에서 이미지 검색 및 다운로드
            search_term = title.split()[0]
            self.pexels.search(search_term, page=1, results_per_page=1)
            photo_url = self.pexels.get_entries()[0].original
            img_data = requests.get(photo_url, timeout=20).content
            
            with open("background.jpg", "wb") as f:
                f.write(img_data)

            # 2. 썸네일 제작
            img = Image.open("background.jpg").resize((1280, 720))
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("/app/fonts/Catfont.ttf", 60)
            
            lines = textwrap.wrap(title, width=25)
            y_text = (720 - (len(lines) * 70)) / 2 # 중앙 정렬
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                x_text = (1280 - (bbox[2] - bbox[0])) / 2
                draw.text((x_text, y_text), line, font=font, fill="#FFFFFF", stroke_width=3, stroke_fill="#000000")
                y_text += 70
            
            thumbnail_path = "thumbnail.png"
            img.save(thumbnail_path)
            logger.info(f"✅ 썸네일 저장 완료: {thumbnail_path}")

            # 3. FFmpeg으로 영상 제작
            with open("script.txt", "w", encoding="utf-8") as f:
                f.write(script.replace(":", "\\:").replace("'", ""))
            
            video_path = "output.mp4"
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", "background.jpg", "-i", "audio.mp3", # 오디오 파일이 있다면 추가
                "-vf", f"fade=t=in:st=0:d=1,fade=t=out:st=57:d=1,drawtext=textfile=script.txt:fontfile=/app/fonts/Catfont.ttf:fontsize=30:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.5:boxborderw=5",
                "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
                "-t", "58", video_path
            ]
            # 오디오 파일이 없을 경우 -i audio.mp3 와 -c:a, -b:a 옵션은 제거해야 합니다.
            # 지금은 오디오 없이 영상만 생성하는 간소화된 버전입니다.
            simplified_cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", "background.jpg", 
                "-vf", f"scale=1080:1920,setsar=1,drawtext=textfile=script.txt:fontfile=/app/fonts/Catfont.ttf:fontsize=40:fontcolor=white:x=(w-text_w)/2:y=h-200:box=1:boxcolor=black@0.5:boxborderw=10",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", "58", video_path
            ]

            subprocess.run(simplified_cmd, check=True, timeout=180)
            logger.info(f"✅ 영상 제작 완료: {video_path}")
            return video_path, thumbnail_path

        except Exception as e:
            logger.error(f"미디어 제작 중 오류 발생: {e}")
            return None, None

    def _upload_to_youtube(self, video_path, thumbnail_path, title, description):
        """제작된 영상과 썸네일을 유튜브에 업로드합니다."""
        logger.info(f"📤 '{title}' 영상 업로드를 시작합니다.")
        try:
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["shorts", "ai", "자동화", "꿀팁"],
                    "categoryId": "28" # 과학 및 기술
                },
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
            }
            
            # 1. 영상 업로드
            request = self.youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
            )
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"업로드 진행률: {int(status.progress() * 100)}%")
            
            video_id = response.get('id')
            logger.info(f"✅ 영상 업로드 완료! Video ID: {video_id}")

            # 2. 썸네일 설정
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            logger.info("✅ 썸네일 설정 완료.")
            return True

        except HttpError as e:
            logger.error(f"유튜브 업로드 중 API 오류 발생: {e}")
            return False

    def run(self):
        """자동화 작업의 전체 흐름을 실행합니다."""
        topics = ["AI 최신 뉴스", "미래 기술 트렌드", "코딩 생산성 팁", "놀라운 과학 사실", "디지털 노마드 라이프"]
        topic = random.choice(topics)
        
        script = self._generate_script(topic)
        if not script: return

        title = self._optimize_title(topic)
        video_path, thumbnail_path = self._create_video_and_thumbnail(title, script)
        if not (video_path and thumbnail_path): return
        
        description = f"{script}\n\n#shorts #AI #자동화 #자기계발"
        success = self._upload_to_youtube(video_path, thumbnail_path, title, description)

        if success:
            logger.info("🎉🎉🎉 모든 작업이 성공적으로 완료되었습니다! 🎉🎉🎉")
        else:
            logger.error("🔥 최종 업로드 과정에서 문제가 발생했습니다.")

if __name__ == "__main__":
    job = YouTubeAutomationJob()
    job.run()
