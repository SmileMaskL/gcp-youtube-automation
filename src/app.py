# src/app.py (이전 내용을 모두 지우고 아래 내용으로 교체하세요!)

import os
import logging
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor

# ✅ AI 및 YouTube API 관련 라이브러리 추가
import google.generativeai as genai # Google Gemini API
from googleapiclient.discovery import build # YouTube Data API
import ffmpeg # FFmpeg 파이썬 래퍼 (pip install ffmpeg-python)
import random # 예시를 위한 임시 import
import time # 예시를 위한 임시 import

# ✅ 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info("✅ 애플리케이션 로깅이 기본 설정되었습니다.")

# ✅ Flask 애플리케이션 인스턴스 생성
app = Flask(__name__)

# ✅ ThreadPoolExecutor 설정
# Cloud Run 환경 변수에서 MAX_WORKERS를 가져오거나, 기본값 4를 사용합니다.
max_app_threads = int(os.getenv('MAX_WORKERS', 4))
executor = ThreadPoolExecutor(max_workers=max_app_threads)
logger.info(f"ThreadPoolExecutor가 {max_app_threads}개의 스레드로 초기화되었습니다.")

# ✅ 작업 상태 저장 딕셔너리 (Cloud Run은 앱 종료 시 초기화되므로, 실제 서비스에서는 DB 사용 권장)
job_status = {}

# --- AI API 및 YouTube API 설정 (환경 변수에서 API 키 가져오기) ---
# Google Gemini API 키 설정
# GitHub Secrets에 GEMINI_API_KEY로 저장해야 합니다.
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# YouTube Data API 설정
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
# 개발자 키는 GitHub Secrets에 YOUTUBE_API_KEY로 저장해야 합니다.
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                developerKey=os.environ.get("YOUTUBE_API_KEY"))

# 수익 창출을 위한 제휴 마케팅 링크 (여기에 당신의 실제 제휴 링크를 넣으세요!)
# 이 링크를 통해 사람들이 구매하면 수익이 발생합니다.
AFFILIATE_LINK = "https://your-affiliate-program.com/link_to_product"
# --- 여기까지 설정 ---

# ✅ Health Check 엔드포인트 (Cloud Run이 앱이 살아있는지 확인하는 주소)
@app.route('/healthz', methods=['GET'])
def health_check():
    logger.info("Health check 요청 수신. 상태: OK")
    return jsonify({"status": "ok"}), 200

# ✅ 작업 상태 확인 엔드포인트 (백그라운드 작업의 진행 상황 확인)
@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    status = job_status.get(job_id)
    if not status:
        logger.warning(f"작업 ID [{job_id}]를 찾을 수 없습니다.")
        return jsonify({"status": "not_found"}), 404
    logger.info(f"작업 ID [{job_id}] 상태 요청: {status['status']}")
    return jsonify(status), 200

# ✅ 메인 엔드포인트 (GitHub Actions에서 이 주소로 POST 요청을 보냅니다)
@app.route("/", methods=["POST"])
def main_endpoint():
    data = request.get_json()
    if not data:
        logger.error("JSON payload가 제공되지 않았습니다.")
        return jsonify({"status": "error", "message": "JSON payload가 제공되지 않았습니다"}), 400

    action = data.get('action', '')
    metadata = data.get('metadata', {}) # 추가 정보 (예: 주제, 키워드 등)

    job_id = str(uuid.uuid4()) # 고유한 작업 ID 생성
    job_status[job_id] = {
        'status': 'queued',
        'metadata': metadata,
        'start_time': datetime.utcnow().isoformat() + 'Z' # UTC 시간으로 저장
    }
    logger.info(f"새로운 작업 요청 수신: ID [{job_id}], Action: {action}")

    if action == 'create_and_upload_shorts':
        # 실제 작업은 백그라운드 스레드에서 실행
        executor.submit(process_youtube_shorts_upload, metadata, job_id)
        return jsonify({
            "status": "processing",
            "job_id": job_id,
            "status_url": f"/status/{job_id}" # 작업 상태를 확인할 수 있는 URL
        }), 202 # 202 Accepted: 요청을 받았고 처리 중임을 알립니다.
    else:
        job_status[job_id]['status'] = 'failed'
        job_status[job_id]['error'] = f"지원되지 않는 액션: {action}"
        job_status[job_id]['end_time'] = datetime.utcnow().isoformat() + 'Z'
        logger.error(f"지원되지 않는 액션 요청: {action}")
        return jsonify({"status": "error", "message": f"지원되지 않는 액션: {action}"}), 400

# --- 핵심 수익 창출 로직 함수들 ---

def generate_script_with_ai(topic="오늘의 명언", model_name="gemini-pro"):
    """
    Google Gemini API를 사용하여 짧은 스크립트를 생성합니다.
    무료 한도 내에서 사용하려면 요청 수를 제한하고, 짧게 생성하도록 프롬프트를 조절하세요.
    """
    try:
        model = genai.GenerativeModel(model_name)
        # 프롬프트: 15초 쇼츠에 맞는 짧고 간결한 한국어 스크립트 요청
        prompt = f"{topic}에 대한 짧고 매력적인 15초 유튜브 쇼츠 스크립트를 한국어로 50자 내외로 작성해줘. 텍스트만."
        response = model.generate_content(prompt)
        script = response.text.strip()
        logger.info(f"AI가 스크립트 생성 완료: {script[:50]}...")
        return script
    except Exception as e:
        logger.error(f"AI 스크립트 생성 실패: {e}")
        return "오늘도 행복한 하루 되세요! 🌟" # 실패 시 기본 스크립트

def create_simple_video(script_text, output_path="output/shorts.mp4"):
    """
    간단한 텍스트 기반 영상을 생성합니다. (FFmpeg 사용)
    쇼츠에 최적화된 세로형 (1080x1920) 영상을 만듭니다.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True) # output 폴더가 없으면 생성
    
    try:
        # FFmpeg 명령어를 사용하여 검은색 배경에 텍스트를 오버레이합니다.
        # 자세한 FFmpeg 설정은 필요에 따라 변경 가능
        (
            ffmpeg
            .input('color=c=black:s=1080x1920', f='lavfi', t=15) # 15초 검은 배경 영상 (세로형, 1080x1920 해상도)
            .drawtext(text=script_text, fontsize=80, fontcolor='white', x='(w-text_w)/2', y='(h-text_h)/2',
                      box=1, boxcolor='black@0.5', boxborderw=20, # 텍스트 배경 상자
                      wrap=True, # 텍스트 자동 줄바꿈
                      line_spacing=20) # 줄 간격 조절
            .output(output_path, pix_fmt='yuv420p', vf='scale=1080:1920') # 쇼츠 사이즈 (세로)
            .run(overwrite_output=True, quiet=True) # quiet=True로 FFmpeg 로그를 줄여줍니다.
        )
        logger.info(f"영상 생성 완료: {output_path}")
        return output_path
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg 영상 생성 실패: {e.stderr.decode()}")
        return None
    except Exception as e:
        logger.error(f"영상 생성 중 예상치 못한 에러 발생: {e}")
        return None

def upload_to_youtube(video_path, title, description, tags):
    """
    생성된 영상을 YouTube에 업로드합니다.
    """
    if not video_path or not os.path.exists(video_path):
        logger.error("업로드할 영상 파일이 유효하지 않거나 존재하지 않습니다.")
        return False

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22",  # People & Blogs 카테고리 (적절히 변경 가능)
            "defaultLanguage": "ko"
        },
        "status": {
            "privacyStatus": "public" # public (공개), private (비공개), unlisted (일부 공개) 중 선택
        }
    }

    # 미디어 파일 (동영상 파일) 업로드
    media = {'body': open(video_path, 'rb')}

    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        response = request.execute()
        logger.info(f"YouTube 업로드 성공! 영상 ID: {response.get('id')}, URL: https://youtu.be/{response.get('id')}")
        return True
    except Exception as e:
        logger.error(f"YouTube 업로드 실패: {e}")
        return False

# ✅ 백그라운드에서 실행될 실제 유튜브 쇼츠 업로드 프로세스
def process_youtube_shorts_upload(metadata, job_id):
    logger.info(f"▶️ [{job_id}] YouTube Shorts 업로드 프로세스 시작. Metadata: {metadata}")
    job_status[job_id]['status'] = 'processing'
    job_status[job_id]['start_time'] = datetime.utcnow().isoformat() + 'Z' # 정확한 시작 시간 업데이트
    created_video_path = None # 에러 발생 시 파일 삭제를 위한 초기화

    try:
        # 1. AI로 스크립트 생성 (예: 오늘의 명언, 뉴스 요약 등)
        script_topic = metadata.get("topic", "하루를 시작하는 긍정적인 명언")
        script = generate_script_with_ai(topic=script_topic)
        if not script:
            raise Exception("AI 스크립트 생성 실패")
        logger.info(f"[{job_id}] 스크립트: {script}")

        # 2. 영상 제목, 설명, 태그 생성 (AI 또는 고정값 조합)
        # 제목은 스크립트 앞부분을 사용하여 매력적으로 만듭니다.
        video_title = f"✨ 오늘의 긍정 에너지: {script[:30]}..." 
        # 설명에 제휴 마케팅 링크를 포함하여 수익 창출 기회를 만듭니다.
        video_description = (
            f"매일 긍정적인 메시지로 하루를 시작하세요! #긍정명언 #동기부여 #쇼츠\n\n"
            f"당신의 하루를 바꿀 수 있는 제품 보러가기: {AFFILIATE_LINK}"
        )
        video_tags = ["명언", "동기부여", "긍정", "쇼츠", "매일명언", script_topic.replace(" ", ""), "유튜브자동화"]
        logger.info(f"[{job_id}] 제목: {video_title}")

        # 3. 영상 생성
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True) # 'output' 폴더가 없으면 생성
        video_file_name = f"daily_shorts_{job_id}.mp4"
        created_video_path = os.path.join(output_dir, video_file_name)
        
        logger.info(f"[{job_id}] 영상 생성 시작: {created_video_path}")
        created_video_path = create_simple_video(script, created_video_path)
        if not created_video_path:
            raise Exception("영상 파일 생성 실패")
        logger.info(f"[{job_id}] 영상 파일 크기: {os.path.getsize(created_video_path) / (1024*1024):.2f} MB")

        # 4. YouTube 업로드
        logger.info(f"[{job_id}] YouTube 업로드 시작.")
        upload_success = upload_to_youtube(created_video_path, video_title, video_description, video_tags)
        
        if not upload_success:
            raise Exception("YouTube 업로드 실패")

        logger.info(f"✅ [{job_id}] 작업 성공적으로 완료됨.")
        job_status[job_id]['status'] = 'completed'
        job_status[job_id]['end_time'] = datetime.utcnow().isoformat() + 'Z'
        job_status[job_id]['message'] = "YouTube Shorts 생성 및 업로드 완료!"

    except Exception as e:
        logger.error(f"❌ [{job_id}] 작업 실패: {e}")
        job_status[job_id]['status'] = 'failed'
        job_status[job_id]['error'] = str(e)
        job_status[job_id]['end_time'] = datetime.utcnow().isoformat() + 'Z'
    finally:
        # 5. 생성된 임시 파일 정리 (GCP 무료 한도 관리를 위해 중요!)
        # 작업 성공/실패 여부와 상관없이 파일을 삭제하여 저장 공간을 확보합니다.
        if created_video_path and os.path.exists(created_video_path):
            os.remove(created_video_path)
            logger.info(f"[{job_id}] 임시 영상 파일 삭제 완료: {created_video_path}")

# ✅ 애플리케이션 종료 시 ThreadPoolExecutor 안전 종료
import atexit
@atexit.register
def shutdown_threadpool():
    logger.info("ThreadPoolExecutor 종료 중...")
    executor.shutdown(wait=True) # 모든 스레드 작업이 끝날 때까지 기다립니다.
    logger.info("ThreadPoolExecutor 종료 완료.")

# ✅ Flask 앱 실행 조건 (로컬 테스트 및 Cloud Run 환경 모두 대비)
# Cloud Run은 PORT 환경 변수를 통해 포트를 지정합니다.
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    # Flask 개발 서버는 운영 환경에 적합하지 않으므로,
    # gunicorn으로 실행될 때 이 블록은 실행되지 않습니다.
    # 로컬에서 'python src/app.py'로 직접 실행할 때만 사용됩니다.
    app.run(host="0.0.0.0", port=port, debug=False)
    logger.info(f"Flask 애플리케이션이 http://0.0.0.0:{port} 에서 실행 중입니다.")
