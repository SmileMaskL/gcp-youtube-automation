# src/video_creator.py
import os
import logging
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from src.utils import download_from_gcs, upload_to_gcs, delete_gcs_file

logger = logging.getLogger(__name__)

def create_video_from_frames(video_gcs_path: str, audio_gcs_path: str, output_path: str, gcp_bucket_name: str):
    """
    GCS에 저장된 배경 영상과 오디오를 결합하여 최종 영상을 생성합니다.
    
    Args:
        video_gcs_path (str): GCS에 저장된 배경 영상 파일의 경로.
        audio_gcs_path (str): GCS에 저장된 오디오 파일의 경로.
        output_path (str): 생성될 최종 영상 파일의 로컬 경로.
        gcp_bucket_name (str): GCP 버킷 이름.
        
    Returns:
        bool: 영상 생성 성공 시 True, 실패 시 False.
    """
    video_local_path = f"/tmp/{os.path.basename(video_gcs_path)}"
    audio_local_path = f"/tmp/{os.path.basename(audio_gcs_path)}"

    try:
        # GCS에서 영상 및 오디오 파일 다운로드
        logger.info(f"Downloading video from GCS: {video_gcs_path} to {video_local_path}")
        if not download_from_gcs(gcp_bucket_name, video_gcs_path, video_local_path):
            logger.error("Failed to download background video from GCS.")
            return False
            
        logger.info(f"Downloading audio from GCS: {audio_gcs_path} to {audio_local_path}")
        if not download_from_gcs(gcp_bucket_name, audio_gcs_path, audio_local_path):
            logger.error("Failed to download audio file from GCS.")
            # 실패하더라도 이미 다운로드된 비디오 파일 삭제
            if os.path.exists(video_local_path):
                os.remove(video_local_path)
            return False

        logger.info(f"Loading video from: {video_local_path}")
        video_clip = VideoFileClip(video_local_path)
        logger.info(f"Loading audio from: {audio_local_path}")
        audio_clip = AudioFileClip(audio_local_path)

        # 오디오 길이에 맞춰 비디오 클립 자르기 또는 반복
        if audio_clip.duration > video_clip.duration:
            # 오디오가 비디오보다 길면 비디오를 반복하여 늘립니다.
            num_repeats = int(audio_clip.duration / video_clip.duration) + 1
            video_clip = concatenate_videoclips([video_clip] * num_repeats)
            logger.info(f"Video clip repeated to match audio duration. New video duration: {video_clip.duration:.2f}s")
        
        # 비디오 클립을 오디오 길이에 맞춰 자릅니다.
        final_video_clip = video_clip.set_audio(audio_clip).set_duration(audio_clip.duration)
        logger.info(f"Final video duration set to audio duration: {final_video_clip.duration:.2f}s")
        
        # 출력 디렉토리 생성
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")

        logger.info(f"Writing final video to: {output_path}")
        final_video_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24, # 프레임 속도 설정 (원하는 값으로 조정 가능)
            preset="fast", # 인코딩 속도 (ultrafast, superfast, fast, medium, slow, slower, veryslow)
            threads=os.cpu_count() or 1, # 사용 가능한 CPU 코어 수 활용
            logger=None # moviepy 로그를 직접 처리하지 않음
        )
        logger.info(f"Video successfully created and saved to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error creating video: {e}", exc_info=True)
        return False
    finally:
        # 다운로드한 임시 파일 삭제
        if os.path.exists(video_local_path):
            os.remove(video_local_path)
            logger.info(f"Removed temporary video file: {video_local_path}")
        if os.path.exists(audio_local_path):
            os.remove(audio_local_path)
            logger.info(f"Removed temporary audio file: {audio_local_path}")
        
        # GCS에 업로드된 원본 파일 삭제 (무료 할당량 관리를 위해)
        delete_gcs_file(gcp_bucket_name, video_gcs_path)
        delete_gcs_file(gcp_bucket_name, audio_gcs_path)

# 테스트용 코드
if __name__ == "__main__":
    from dotenv import load_dotenv
    from src.config import setup_logging
    from src.utils import upload_to_gcs, download_from_gcs, delete_gcs_file
    
    load_dotenv()
    setup_logging()

    # 이 테스트는 실제 GCS 버킷과 유효한 mp4, mp3 파일이 필요합니다.
    # 테스트용 더미 파일 생성 (실제 파일이 아님)
    # import tempfile
    # temp_video_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    # temp_audio_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    # print(f"Created dummy files: {temp_video_file.name}, {temp_audio_file.name}")
    # temp_video_file.close()
    # temp_audio_file.close()
    
    # 실제 테스트를 위해서는 실제 비디오/오디오 파일을 사용하거나,
    # 테스트용 작은 비디오/오디오 파일을 만들어 GCS에 업로드해야 합니다.
    
    # 예시 (실제 파일을 가정):
    # test_bucket = os.environ.get("GCP_BUCKET_NAME")
    # if not test_bucket:
    #     print("Set GCP_BUCKET_NAME environment variable for test.")
    # else:
    #     # GCS에 미리 업로드된 테스트 파일 사용 예시
    #     test_video_gcs = "test_data/sample_video.mp4"
    #     test_audio_gcs = "test_data/sample_audio.mp3"
    #     test_output_path = "output/test_created_video.mp4"
        
    #     # 로컬에 테스트용 더미 파일 생성 및 GCS에 업로드하는 로직 (실제 테스트용)
    #     # ... (여기서 샘플 영상과 오디오를 생성하거나 다운로드하여 GCS에 업로드)
    #     # Example: Assume a sample.mp4 and sample.mp3 exist locally for initial upload
    #     # upload_to_gcs(test_bucket, "sample.mp4", test_video_gcs)
    #     # upload_to_gcs(test_bucket, "sample.mp3", test_audio_gcs)
        
    #     if create_video_from_frames(test_video_gcs, test_audio_gcs, test_output_path, test_bucket):
    #         print(f"Test video created successfully at {test_output_path}")
    #     else:
    #         print("Test video creation failed.")
            
    #     # 테스트 후 GCS의 임시 파일 삭제 (선택 사항)
    #     # delete_gcs_file(test_bucket, test_video_gcs)
    #     # delete_gcs_file(test_bucket, test_audio_gcs)
    
    print("\nNote: This test requires sample video and audio files to be available/uploaded to GCS.")
    print("Please manually provide or generate small test media files for thorough testing.")
