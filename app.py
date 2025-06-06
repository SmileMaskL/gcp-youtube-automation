import os
import tempfile
from flask import Flask, request, jsonify

from moviepy.editor import TextClip
import openai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 환경변수에서 서비스 키를 받아서 사용 (Cloud Run 환경변수로 등록 필요)
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
YOUTUBE_REFRESH_TOKEN = os.getenv('YOUTUBE_REFRESH_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)

def get_openai_text(prompt):
    openai.api_key = OPENAI_API_KEY
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content.strip()

def make_video_from_text(text, outfile):
    # 30초짜리 검정배경 텍스트 영상 생성
    clip = TextClip(text, fontsize=40, color='white', size=(720,1280), bg_color='black', method='caption')
    clip = clip.set_duration(30)
    clip.write_videofile(outfile, fps=24, codec="libx264", audio=False)

def get_youtube_service():
    # Cloud Run에서는 Refresh Token 기반 인증이 안정적 (서버리스 환경)
    creds = Credentials(
        token=None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(title, description, video_file):
    youtube = get_youtube_service()
    body=dict(
        snippet=dict(
            title=title,
            description=description,
            tags=["AI","Shorts","자동수익"]
        ),
        status=dict(
            privacyStatus="public"
        )
    )
    media = MediaFileUpload(video_file, mimetype='video/mp4', resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    response = request.execute()
    return response.get("id")

@app.route('/upload', methods=['POST'])
def upload():
    prompt = request.json.get('prompt') or "AI가 돈 버는 방법에 대한 유튜브 스크립트 30초 분량으로 만들어줘."
    try:
        script_text = get_openai_text(prompt)
    except Exception as e:
        return jsonify({"error": "AI 대본 생성 실패", "raw": str(e)}), 500

    # 임시 저장소에 동영상 저장
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tf:
        outpath = tf.name
    try:
        make_video_from_text(script_text, outpath)
    except Exception as e:
        return jsonify({"error": "동영상 생성 실패", "raw": str(e)}), 500

    # YouTube 업로드
    try:
        youtube_title = "AI 수익
