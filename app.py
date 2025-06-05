from flask import Flask, request, jsonify
import logging
import os
import time
import traceback
from threading import Thread
from datetime import datetime, timedelta

# src 모듈 임포트
from src.video_creator import create_video
from src.youtube_uploader import upload_video
from src.utils import get_trending_topics, get_secret, rotate_api_key, clean_old_data
from src.thumbnail_generator import generate_thumbnail
from src.comment_poster import post_comment
from src.shorts_converter import convert_to_shorts

app = Flask(__name__)

# 로깅 설정
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

logging.basicConfig(
    filename=os.path.join(LOGS_DIR, "automation.log"),
    level=logging.110,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler()) # 콘솔 출력 추가

# 락 파일 타임아웃 (1시간)
LOCK_TIMEOUT = 3600

@app.route('/run', methods=['POST'])
def run_automation():
    data = request.get_json() or {}
    trigger_source = data.get('trigger', 'manual')
    logger.info(f"🚀 자동화 요청 수신 ({trigger_source} 트리거)")

    try:
        # 락 파일 확인 및 타임아웃 처리
        lock_file_path = 'running.lock'
        if os.path.exists(lock_file_path):
            lock_age = time.time() - os.path.getmtime(lock_file_path)
            if lock_age < LOCK_TIMEOUT:
                logger.warning("⚠️ 이미 실행 중인 작업 존재. 락 파일이 유효합니다.")
                return jsonify({"status": "rejected", "message": "작업 실행 중"}), 429
            else:
                logger.warning("⚠️ 오래된 락 파일 발견. 강제 제거 후 재실행.")
                os.remove(lock_file_path)
                
        # 잠금 파일 생성
        with open(lock_file_path, 'w') as f:
            f.write(str(time.time()))
            
        # 백그라운드 작업 시작
        thread = Thread(target=background_task)
        thread.start()
        
        logger.info("✅ 수익 생성 작업 시작됨.")
        return jsonify({
            "status": "started",
            "message": "수익 생성 작업 시작됨",
            "next_step": "영상 제작 중",
            "estimated_time": "5-15분 소요 예정"
        }), 202
        
    except Exception as e:
        error_detail = f"🔴 엔드포인트 오류: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)
        
        # 오류 발생 시 락 파일 제거
        if os.path.exists(lock_file_path):
            os.remove(lock_file_path)
            logger.info("🔓 시스템 잠금 해제 (오류로 인한)")
            
        return jsonify({"status": "error", "message": "시스템 오류 발생", "detail": str(e)}), 500

def background_task():
    try:
        logger.info("🔄 백그라운드 작업 시작")
        
        # 0. 오래된 데이터 정리 (클라우드 스토리지 용량 관리)
        clean_old_data()
        logger.info("🧹 오래된 데이터 정리 완료.")

        # 1. 트렌드 분석 (실시간 인기 주제 확보)
        trends = get_trending_topics()
        topic = trends[0]['title'] if trends else "AI 기술 동향"
        logger.info(f"🔥 선택 주제: {topic} (예상 조회수: 50만+ 목표)")
        
        # 2. 콘텐츠 생성 (스크립트, 제목, 설명 등)
        # content_generator.py에서 generate_content 함수를 호출
        # rotate_api_key는 content_generator 내부에서 호출되도록 설계
        content_generator = YouTubeAutomation() # 인스턴스 생성
        generated_content = content_generator.generate_content(topic) # content_generator의 generate_content 사용

        # 3. 영상 제작 (음성, 이미지, 텍스트 합성)
        # video_creator.py의 create_video 함수는 이미 content_generator에서 통합되어 있음
        # 하지만 기존 구조를 유지하기 위해 직접 호출하는 방식으로 변경
        video_path = create_video(topic, generated_content['script'], generated_content['title_text']) # 스크립트와 제목 텍스트 전달
        logger.info(f"🎬 영상 생성 완료: {video_path}")
        
        # 4. 썸네일 생성
        thumbnail_path = generate_thumbnail(video_path, generated_content['title_text']) # 썸네일에도 제목 텍스트 사용
        if thumbnail_path:
            logger.info(f"🖼️ 썸네일 생성 완료: {thumbnail_path}")
        else:
            logger.warning("⚠️ 썸네일 생성 실패. 기본 썸네일로 업로드됩니다.")

        # 5. Shorts 변환
        shorts_path = convert_to_shorts(video_path)
        logger.info(f"✂️ Shorts 변환 완료: {shorts_path}")
        
        # 6. 유튜브 업로드 (Shorts 버전)
        video_url = upload_video(
            file_path=shorts_path, # Shorts 영상 업로드
            title=f"{generated_content['title']} │ #Shorts",
            description=f"{generated_content['description']}\n\n이 영상은 AI로 자동 생성되었습니다. 구독과 좋아요 부탁드려요! :)",
            thumbnail_path=thumbnail_path
        )
        logger.info(f"📤 업로드 성공: {video_url}")
        
        # 7. 댓글 작성
        if video_url:
            # video_url에서 video_id 추출
            video_id = video_url.split("v=")[-1].split("&")[0] if "v=" in video_url else video_url.split("/")[-1]
            if post_comment(video_id, "이 영상은 AI로 자동 생성되었습니다! 재미있게 보셨다면 구독 부탁드려요 :)"):
                logger.info(f"💬 댓글 작성 완료: {video_id}")
            else:
                logger.warning(f"💬 댓글 작성 실패: {video_id}")
        
        # 8. 수익 분석 기록
        with open("revenue_log.csv", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')},{topic},{video_url}\n")
        logger.info("💰 수익 창출 완료! 예상 수익: $500~$2000/월 목표")
        
    except Exception as e:
        logger.error(f"🔴 백그라운드 작업 실패: {str(e)}\n{traceback.format_exc()}")
        
    finally:
        # 잠금 해제
        lock_file_path = 'running.lock'
        if os.path.exists(lock_file_path):
            os.remove(lock_file_path)
        logger.info("🔓 시스템 잠금 해제")
        
        # 생성된 임시 파일 및 영상 파일 삭제 (용량 관리)
        try:
            if 'video_path' in locals() and os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"🗑️ 원본 영상 파일 삭제: {video_path}")
            if 'shorts_path' in locals() and os.path.exists(shorts_path):
                os.remove(shorts_path)
                logger.info(f"🗑️ Shorts 영상 파일 삭제: {shorts_path}")
            if 'thumbnail_path' in locals() and os.path.exists(thumbnail_path) and thumbnail_path != "temp_thumbnail.jpg": # 기본 썸네일은 삭제 안 함
                os.remove(thumbnail_path)
                logger.info(f"🗑️ 썸네일 파일 삭제: {thumbnail_path}")
        except Exception as cleanup_e:
            logger.warning(f"⚠️ 파일 정리 중 오류 발생: {cleanup_e}")


if __name__ == '__main__':
    # 클라우드 배포용 설정
    app.run(
        debug=False,
        host='0.0.0.0',
        port=8080,
        threaded=True  # 동시 요청 처리 활성화
    )
