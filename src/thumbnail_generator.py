# src/thumbnail_generator.py
import os
import logging
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)

def generate_thumbnail(video_path: str, thumbnail_path: str, time_in_seconds: float = 2.0):
    """
    동영상에서 특정 시간의 프레임을 추출하여 썸네일로 저장합니다.

    Args:
        video_path (str): 썸네일을 추출할 동영상 파일의 경로.
        thumbnail_path (str): 생성될 썸네일 이미지 파일의 경로.
        time_in_seconds (float): 썸네일을 추출할 동영상의 시간(초).

    Returns:
        bool: 썸네일 생성 성공 시 True, 실패 시 False.
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found for thumbnail generation: {video_path}")
        return False

    try:
        logger.info(f"Generating thumbnail for {video_path} at {time_in_seconds} seconds.")
        clip = VideoFileClip(video_path)

        # 영상 길이를 초과하지 않도록 시간 조정
        if time_in_seconds >= clip.duration:
            time_in_seconds = clip.duration / 2 # 영상 중간으로 설정
            logger.warning(f"Thumbnail time adjusted to video's mid-point: {time_in_seconds:.2f}s")

        # 출력 디렉토리 생성
        output_dir = os.path.dirname(thumbnail_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")

        clip.save_frame(thumbnail_path, t=time_in_seconds)
        logger.info(f"Thumbnail saved to {thumbnail_path}")
        return True
    except Exception as e:
        logger.error(f"Error generating thumbnail for {video_path}: {e}", exc_info=True)
        return False

if __name__ == '__main__':
    from src.config import setup_logging
    setup_logging()

    # 테스트용 더미 영상 파일이 필요합니다.
    # 이전에 `shorts_converter.py` 테스트 시 생성된 `output/test_shorts_output.mp4`를 사용할 수 있습니다.
    input_test_video = "output/test_shorts_output.mp4" # 여기에 실제 테스트 영상 파일 경로를 지정하세요.
    output_test_thumbnail = "output/test_generated_thumbnail.jpg"

    if not os.path.exists(input_test_video):
        print(f"Error: Test video file not found at '{input_test_video}'. Please ensure it exists.")
    else:
        print(f"Attempting to generate thumbnail for '{input_test_video}'...")
        if generate_thumbnail(input_test_video, output_test_thumbnail, time_in_seconds=5.0):
            print(f"Successfully generated thumbnail: {output_test_thumbnail}")
        else:
            print("Failed to generate thumbnail.")
