import os
import datetime
from src.content_generator import get_trending_topic, generate_video_script, generate_video_title, generate_video_description, generate_video_tags, generate_youtube_comments, generate_short_summary
from src.bg_downloader import download_background
from src.tts_generator import generate_audio
from src.video_editor import create_video
from src.thumbnail_generator import create_thumbnail
from src.youtube_uploader import upload_video, post_comment
from src.cleanup_manager import cleanup_gcs_bucket
from src.monitoring import log_system_health, upload_log_to_gcs
from src.config import OUTPUT_DIR, LOG_DIR, GCS_BUCKET_NAME
import shutil
import time

def process_single_video(video_number):
    """단일 유튜브 Shorts 영상 생성 및 업로드 프로세스."""
    log_system_health(f"--- 영상 #{video_number} 처리 시작 ---", level="info")

    try:
        # 1. 최신 트렌드 토픽 가져오기
        topic = get_trending_topic()
        log_system_health(f"획득된 트렌드 토픽: {topic}", level="info")

        # 2. 영상 스크립트 생성
        script = generate_video_script(topic)
        if not script:
            raise ValueError("스크립트 생성 실패.")
        log_system_health(f"생성된 스크립트:\n{script}", level="info")

        # 3. 배경 이미지 다운로드
        background_image_filename = f"background_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{video_number}.jpg"
        background_path = download_background(keyword=topic, output_filename=background_image_filename)
        if not background_path:
            raise ValueError("배경 이미지 다운로드 실패.")
        log_system_health(f"다운로드된 배경 이미지: {background_path}", level="info")

        # 4. 음성 생성
        audio_filename = f"audio_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{video_number}.mp3"
        audio_path = generate_audio(script, output_filename=audio_filename)
        if not audio_path:
            raise ValueError("오디오 생성 실패.")
        log_system_health(f"생성된 오디오: {audio_path}", level="info")

        # 5. 비디오 생성
        video_filename = f"shorts_video_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{video_number}.mp4"
        video_path = create_video(audio_path, background_path, output_filename=video_filename)
        if not video_path:
            raise ValueError("비디오 생성 실패.")
        log_system_health(f"생성된 비디오: {video_path}", level="info")

        # 6. 영상 제목, 설명, 태그, 썸네일 요약 텍스트, 댓글 생성
        title = generate_video_title(script, topic)
        description = generate_video_description(script, title, topic)
        tags = generate_video_tags(topic, title)
        thumbnail_summary = generate_short_summary(script)
        generated_comments = generate_youtube_comments(title, num_comments=3) # 3개 댓글 생성

        log_system_health(f"생성된 제목: {title}", level="info")
        log_system_health(f"생성된 설명: {description}", level="info")
        log_system_health(f"생성된 태그: {tags}", level="info")
        log_system_health(f"생성된 썸네일 요약: {thumbnail_summary}", level="info")
        log_system_health(f"생성된 댓글: {generated_comments}", level="info")

        # 7. 썸네일 생성
        thumbnail_filename = f"thumbnail_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{video_number}.jpg"
        thumbnail_path = create_thumbnail(thumbnail_summary, background_path, output_filename=thumbnail_filename)
        if not thumbnail_path:
            raise ValueError("썸네일 생성 실패.")
        log_system_health(f"생성된 썸네일: {thumbnail_path}", level="info")

        # 8. YouTube에 업로드
        uploaded_video_id = upload_video(video_path, thumbnail_path, title, description, tags)
        if not uploaded_video_id:
            raise ValueError("YouTube 업로드 실패.")
        log_system_health(f"비디오가 YouTube에 성공적으로 업로드되었습니다. ID: {uploaded_video_id}", level="info")

        # 9. 댓글 포스팅
        for comment_text in generated_comments:
            try:
                post_comment(uploaded_video_id, comment_text)
                log_system_health(f"댓글 '{comment_text}' 포스팅 완료.", level="info")
            except Exception as e:
                log_system_health(f"댓글 포스팅 중 오류 발생: {e}", level="error")

        log_system_health(f"--- 영상 #{video_number} 처리 완료 ---", level="info")
        return True

    except Exception as e:
        log_system_health(f"영상 #{video_number} 처리 중 치명적인 오류 발생: {e}", level="critical")
        return False

def main():
    log_system_health("자동화 프로세스 시작.", level="info")

    # 출력 및 로그 디렉토리 생성
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "backgrounds"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "audio"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "videos"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "thumbnails"), exist_ok=True)

    # 시스템 로그 파일을 이 특정 실행의 로그 파일로 설정
    log_file_path = os.path.join(LOG_DIR, f"automation_run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    # 실제 로깅 핸들러는 src/monitoring.py에서 초기화되므로,
    # 이 변수는 GCS 업로드 시 로그 파일 경로로 사용됩니다.

    # 하루 5개의 Shorts 영상 생성 목표 (시간표 0 3,7,12,18,22 * * * 고려)
    # 매 스케줄 실행 시마다 1개의 영상을 생성하도록 로직 변경
    # GitHub Actions 스케줄러가 여러 번 트리거되므로, 1회 트리거당 1개 영상 생성으로 충분.
    # 즉, main.yml에서 5번의 스케줄을 설정하면 하루에 5개 생성 가능.
    num_videos_to_create = int(os.getenv("NUM_VIDEOS_PER_RUN", "1")) # 기본 1개 생성

    for i in range(1, num_videos_to_create + 1):
        success = process_single_video(i)
        if not success:
            log_system_health(f"영상 #{i} 생성 및 업로드 실패. 다음 영상으로 넘어갑니다.", level="error")

        # 다음 영상 생성을 위해 잠시 대기 (API Rate Limit 및 자원 소모 방지)
        if i < num_videos_to_create:
            log_system_health(f"{i}번째 영상 처리 완료. 다음 영상 처리를 위해 10분 대기...", level="info")
            time.sleep(600) # 10분 대기

    # 모든 작업 완료 후 로컬 생성 파일 정리 및 GCS에 로그 업로드
    log_system_health("모든 영상 처리 완료. 로컬 출력 파일 정리 및 로그 업로드 시작.", level="info")

    # 임시 파일 및 결과물 GCS에 업로드 후 로컬에서 삭제
    # GCS에 업로드할 로그 파일 이름
    gcs_log_blob_name = f"logs/automation_run_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.log"
    # 현재 실행의 로그를 GCS에 업로드
    # Cloud Logging으로 이미 로그가 전송되므로, 파일 자체를 업로드하는 것은 선택 사항
    # 여기서는 파일 기반 로깅을 가정하고 업로드 로직 유지.
    # 실제 GitHub Actions에서는 Cloud Logging으로 충분합니다.

    # 로컬 아웃풋 디렉토리 정리 (선택 사항: 디버깅을 위해 남겨둘 수도 있음)
    # if os.path.exists(OUTPUT_DIR):
    #     shutil.rmtree(OUTPUT_DIR)
    #     log_system_health(f"로컬 '{OUTPUT_DIR}' 디렉토리 정리 완료.", level="info")
    # else:
    #     log_system_health(f"로컬 '{OUTPUT_DIR}' 디렉토리가 존재하지 않습니다.", level="info")

    # GCP Cloud Storage 버킷 정리 (7일 이상 된 파일 삭제)
    try:
        cleanup_gcs_bucket(days_old=7)
    except Exception as e:
        log_system_health(f"GCS 버킷 정리 중 오류 발생: {e}", level="error")

    log_system_health("자동화 프로세스 완료.", level="info")

if __name__ == "__main__":
    main()
