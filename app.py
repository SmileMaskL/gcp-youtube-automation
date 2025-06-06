import os
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import random
import logging
from datetime import datetime

app = Flask(__name__)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/upload', methods=['POST'])
def upload_video():
    try:
        logger.info("영상 생성 시작")
        
        # 1. 동영상 생성 (58초 쇼츠)
        video_path = create_video()
        
        # 2. 유튜브 업로드
        youtube = build('youtube', 'v3', developerKey=os.getenv('YT_API_KEY'))
        
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": f"수익 자동화 {datetime.now().strftime('%m%d')} #{random.randint(1000,9999)}",
                    "description": "#쇼츠 #수익창출 #자동화\n매일 자동 업로드되는 영상입니다",
                    "tags": ["수익", "자동화", "파이썬", "쇼츠", "유튜브수익"]
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False
                }
            },
            media_body=MediaFileUpload(video_path)
        )
        response = request.execute()
        
        # 3. 광고 설정 (수익화)
        youtube.videos().update(
            part="monetizationDetails",
            body={
                "id": response['id'],
                "monetizationDetails": {
                    "access": {"allowed": True}
                }
            }
        ).execute()
        
        logger.info(f"업로드 성공! 영상 ID: {response['id']}")
        return jsonify({"status": "success", "video_id": response['id']}), 200
        
    except Exception as e:
        logger.error(f"에러 발생: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def create_video():
    """간단한 영상 생성 (실제로는 더 복잡한 로직)"""
    output_path = "output.mp4"
    
    # 배경 영상 (480p로 리사이즈)
    clip = VideoFileClip("background.mp4").subclip(0, 58).resize(height=480)
    
    # 텍스트 추가
    text = TextClip("수익 자동화 시스템", fontsize=40, color='white', 
                   stroke_color='black', stroke_width=1)
    text = text.set_position('center').set_duration(58)
    
    # 영상 합성
    final = CompositeVideoClip([clip, text])
    final.write_videofile(output_path, fps=24, threads=4, bitrate="500k")
    
    return output_path

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
