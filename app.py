import os
import random
import time
from datetime import datetime, timedelta
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import openai
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageDraw, ImageFont
import textwrap
import requests
from pexels_api import API
import subprocess
import google.generativeai as genai
OPTIMAL_UPLOAD_HOUR = 9

# 환경 설정
OPENAI_KEYS = os.getenv('OPENAI_API_KEYS', '').split(',')
PEXELS_KEY = os.getenv('PEXELS_API_KEY', '')
YT_CREDS = {
    'client_id': os.getenv('YOUTUBE_CLIENT_ID', ''),
    'client_secret': os.getenv('YOUTUBE_CLIENT_SECRET', ''),
    'refresh_token': os.getenv('YOUTUBE_REFRESH_TOKEN', '')
}

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 수익 극대화 설정
DAILY_UPLOAD_LIMIT = 5    # 일 1개 영상
VIDEO_DURATION = 58.5     # 최적 영상 길이 (58.5초)

class YouTubeAutoUploader:
    def __init__(self):
        self.current_key = random.choice(OPENAI_KEYS)
        openai.api_key = self.current_key
        genai.configure(api_key=os.getenv('GEMINI_API_KEY', ''))
        self.gemini = genai.GenerativeModel('gemini-pro')
        self.pexels = API(PEXELS_KEY)
        self.youtube = self._setup_youtube()
        self.last_upload = None
        self.upload_count_today = 0

    def _setup_youtube(self):
        creds = Credentials.from_authorized_user_info({
            **YT_CREDS,
            'token_uri': 'https://oauth2.googleapis.com/token',
            'scopes': ['https://www.googleapis.com/auth/youtube.upload']
        })
        return build('youtube', 'v3', credentials=creds)

    def _rotate_key(self):
        available = [k for k in OPENAI_KEYS if k != self.current_key]
        if available:
            self.current_key = random.choice(available)
            openai.api_key = self.current_key
            logger.info(f"키 변경: ...{self.current_key[-4:]}")

    def _generate_content(self, topic):
        """GPT-4o와 Gemini를 번갈아가며 사용하는 스마트 생성"""
        try:
            # 무료 모델 우선 사용 (비용 절감)
            if random.random() < 0.7:  # 70% 확률로 Gemini 사용
                response = self.gemini.generate_content(
                    f"60초 YouTube 쇼츠 스크립트 생성:\n"
                    f"주제: {topic}\n"
                    "구조:\n"
                    "1. 초반 5초 강력한 훅\n"
                    "2. 3가지 핵심 포인트\n"
                    "3. 구독 유도 CTA\n"
                    "4. 해시태그: #shorts #viral #자동화\n"
                    "⚠️ 반드시 55-58초 길이로 생성"
                )
                return response.text
            else:  # 30% 확률로 GPT-4o 사용
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "당신은 바이럴 YouTube 쇼츠 전문 작가입니다. 60초 이내 완성도 높은 콘텐츠를 생성하세요."
                        },
                        {
                            "role": "user",
                            "content": f"[{topic}] 주제로 다음 요소 포함:\n"
                            "- 초반 5초: 충격적인 사실\n"
                            "- 중간: 3가지 핵심 포인트\n"
                            "- 끝: 구독 유도\n"
                            "- 해시태그: #shorts #viral #자동화"
                        }
                    ],
                    temperature=0.9,
                    max_tokens=500
                )
                return response.choices[0].message['content']
        except Exception as e:
            logger.error(f"콘텐츠 생성 실패: {str(e)}")
            self._rotate_key()
            return self._generate_content(topic)

    def _optimize_title(self, title):
        """무료 Gemini로 제목 최적화"""
        try:
            response = self.gemini.generate_content(
                f"이 제목을 더 클릭 유도하게 바꿔주세요:\n{title}\n"
                "규칙:\n"
                "- 이모지 2개 이상 포함\n"
                '- 숫자 사용 (예: "3가지 비밀")\n'
                '- 강력한 형용사 사용 (예: "믿을 수 없는")\n'
                '- 길이: 50자 이내'
            )
            return response.text.strip('"')
        except:
            return title + " 🔥🤯"

    def _make_thumbnail(self, title):
        try:
            self.pexels.search(title.split()[0], page=1, results_per_page=1)
            photo = self.pexels.get_entries()[0]
            img = requests.get(photo.original, timeout=10).content
            
            with open("bg.jpg", "wb") as f:
                f.write(img)
            
            img = Image.open("bg.jpg").resize((1280, 720))
            draw = ImageDraw.Draw(img)
            font_size = 60 if len(title) < 25 else 40
            font = ImageFont.truetype("fonts/Catfont.ttf", font_size)
            
            lines = textwrap.wrap(title, width=20)
            y = 180
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                x = (1280 - w) / 2
                
                draw.text((x-2, y-2), line, font=font, fill="black")
                draw.text((x+2, y+2), line, font=font, fill="black")
                draw.text((x, y), line, font=font, fill="#FFD700")
                y += h + 15
            
            thumb_path = "thumbnail.png"
            img.save(thumb_path)
            return thumb_path
        except Exception as e:
            logger.error(f"썸네일 실패: {str(e)}")
            return None

    def _create_video(self, script):
        try:
            with open("script.txt", "w", encoding="utf-8") as f:
                f.write(script)
            
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "color=c=blue:s=1280x720:d=60",
                "-i", "thumbnail.png",
                "-filter_complex", 
                "[0:v][1:v]overlay=0:0,drawtext=textfile=script.txt:fontfile=fonts/Catfont.ttf:fontsize=24:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:a", "aac", "output.mp4"
            ]
            
            subprocess.run(cmd, check=True, timeout=300)
            return "output.mp4"
        except Exception as e:
            logger.error(f"동영상 생성 실패: {str(e)}")
            return None

    def _upload_video(self, file_path, title, desc, tags):
        for attempt in range(3):
            try:
                request = self.youtube.videos().insert(
                    part="snippet,status",
                    body={
                        "snippet": {
                            "title": title,
                            "description": desc[:5000],
                            "tags": tags,
                            "categoryId": "28"
                        },
                        "status": {
                            "privacyStatus": "public",
                            "selfDeclaredMadeForKids": False
                        }
                    },
                    media_body=MediaFileUpload(file_path, resumable=True)
                )
                
                response = None
                while not response:
                    status, response = request.next_chunk()
                    if status:
                        logger.info(f"업로드 진행률: {int(status.progress() * 100)}%")
                
                logger.info(f"업로드 완료! ID: {response['id']}")
                return response['id']
            except HttpError as e:
                logger.error(f"업로드 시도 {attempt + 1} 실패: {str(e)}")
                if attempt == 2:
                    return None
                time.sleep(10)

    def _get_topics(self):
        return [
            "AI 최신 뉴스", "기술 팁", "코딩 비법",
            "생산성 향상", "과학 사실", "생활 개선",
            "미래 기술", "프로그래밍 기술", "디지털 노마드"
        ]

    def upload_daily(self):
        # 업로드 제한 확인
        if self.upload_count_today >= DAILY_UPLOAD_LIMIT:
            logger.info("일일 업로드 한도 도달")
            return False
            
        # 최적 시간 확인 (한국 시간 기준)
        current_hour = datetime.utcnow().hour + 9
        if current_hour >= 24: current_hour -= 24
        if abs(current_hour - OPTIMAL_UPLOAD_HOUR) > 1:
            logger.info(f"최적 업로드 시간 아님 (현재: {current_hour}시, 권장: {OPTIMAL_UPLOAD_HOUR}시)")
            return False
            
        # 마지막 업로드 확인
        if self.last_upload and (datetime.utcnow() - self.last_upload) < timedelta(hours=20):
            logger.info("너무 빨리 업로드 시도")
            return False
            
        try:
            topic = random.choice(self._get_topics())
            logger.info(f"주제 선택: {topic}")
            
            script = self._generate_content(topic)
            title = self._optimize_title(f"{topic} - {datetime.now().strftime('%m/%d')}")
            thumb = self._make_thumbnail(title)
            
            if not thumb:
                raise Exception("썸네일 생성 실패")
            
            video = self._create_video(script)
            if not video:
                raise Exception("동영상 생성 실패")
            
            video_id = self._upload_video(
                video,
                title,
                f"{script}\n\n#shorts #viral #trending",
                [topic.replace(" ", ""), "shorts", "자동화"]
            )
            
            if video_id:
                self.youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumb)
                ).execute()
                
                # 조회수 부스팅 시도
                try:
                    requests.get(
                        f"https://www.youtube.com/watch?v={video_id}",
                        timeout=3,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                except:
                    pass
                
                self.last_upload = datetime.utcnow()
                self.upload_count_today += 1
                logger.info(f"성공적으로 업로드: {title}")
                return True
        except Exception as e:
            logger.error(f"일일 업로드 실패: {str(e)}")
        return False

if __name__ == "__main__":
    uploader = YouTubeAutoUploader()
    uploader.upload_daily()
