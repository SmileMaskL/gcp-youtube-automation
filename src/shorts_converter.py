# src/shorts_converter.py
import os
import logging
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip, vfx
from moviepy.config import change_settings # moviepy ImageMagick 설정 변경
import sys

logger = logging.getLogger(__name__)

# ImageMagick 경로 설정 (로컬 개발 환경에서 필요할 수 있습니다. Docker에서는 잘 설정되어 있을 것입니다.)
# change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"}) 

def convert_to_shorts(input_video_path: str, output_video_path: str, font_path: str = "fonts/Catfont.ttf"):
    """
    주어진 영상을 YouTube Shorts 형식 (세로, 60초 이내, 텍스트 오버레이)으로 변환합니다.
    
    Args:
        input_video_path (str): 원본 동영상 파일의 경로.
        output_video_path (str): Shorts로 변환된 동영상을 저장할 경로.
        font_path (str): 사용할 폰트 파일의 경로 (고양이체 폰트).
        
    Returns:
        bool: 변환 성공 시 True, 실패 시 False.
    """
    if not os.path.exists(input_video_path):
        logger.error(f"Input video file not found: {input_video_path}")
        return False
    
    if not os.path.exists(font_path):
        logger.error(f"Font file not found: {font_path}. Please ensure Catfont.ttf is in the 'fonts/' directory.")
        # 기본 폰트 사용 또는 에러 처리
        font_path = "DejaVuSans-Bold" # MoviePy 기본 폰트
        logger.warning(f"Using default font: {font_path} due to missing custom font.")

    try:
        logger.info(f"Loading video clip from: {input_video_path}")
        clip = VideoFileClip(input_video_path)
        
        # Shorts는 보통 세로 비율 (9:16)
        # 원본 영상이 가로 비율이면 중앙을 잘라 세로 비율로 만듭니다.
        # 원본 영상이 이미 세로 비율이거나, 세로로 만들기에 부적합하면,
        # 검은색 배경을 추가하여 세로 비율을 맞출 수 있습니다.
        
        # 일반적인 Shorts 해상도: 1080x1920 (width x height)
        target_width = 1080
        target_height = 1920

        # 비디오 리사이징 및 크롭
        # 비디오의 가로/세로 비율을 계산
        aspect_ratio = clip.w / clip.h

        if aspect_ratio > (target_width / target_height): # 비디오가 너무 넓음 (가로형)
            # 세로 비율에 맞춰 높이를 조절하고, 중앙을 크롭
            new_height = target_height
            new_width = int(new_height * aspect_ratio) # 새로운 높이에 맞춰 너비 조절
            temp_clip = clip.resize(height=new_height).crop(
                x_center=clip.w / 2, y_center=clip.h / 2,
                width=target_width, height=target_height
            )
            logger.info(f"Cropped wide video to {target_width}x{target_height}")
        elif aspect_ratio < (target_width / target_height): # 비디오가 너무 좁음 (세로형인데 Shorts보다 좁음)
            # 너비를 조절하고, 양쪽에 검은색 바 추가
            new_width = target_width
            new_height = int(new_width / aspect_ratio)
            temp_clip = clip.resize(width=new_width)
            
            # 검은색 배경 클립 생성
            black_background = ColorClip((target_width, target_height), color=(0,0,0)).set_duration(temp_clip.duration)
            
            # 비디오를 중앙에 배치
            final_clip = CompositeVideoClip([black_background, temp_clip.set_pos("center")]).set_duration(temp_clip.duration)
            logger.info(f"Added black bars to narrow video. Resulting resolution: {target_width}x{target_height}")
            clip = final_clip
        else: # 이미 Shorts 비율
            clip = clip.resize((target_width, target_height))
            logger.info(f"Resized video to {target_width}x{target_height}")

        # Shorts는 최대 60초
        if clip.duration > 60:
            clip = clip.subclip(0, 60) # 60초로 자르기
            logger.info("Clipped video to 60 seconds for Shorts.")

        # 선택 사항: 텍스트 오버레이 (예시)
        # 이 부분은 필요에 따라 batch_processor.py에서 동적으로 콘텐츠 스크립트를 가져와 오버레이할 수 있습니다.
        # 지금은 단순히 "YouTube Shorts" 텍스트를 추가하는 예시입니다.
        text_content = "Generated YouTube Shorts"
        text_clip = TextClip(text_content, 
                             fontsize=70, 
                             color='white', 
                             font=font_path,
                             stroke_color='black', stroke_width=2,
                             method='caption',
                             size=(clip.w * 0.8, None) # 클립 너비의 80%
                            ).set_position(('center', 'top')).set_duration(clip.duration).set_opacity(0.8)

        final_clip = CompositeVideoClip([clip, text_clip])

        # 출력 디렉토리 생성
        output_dir = os.path.dirname(output_video_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")

        logger.info(f"Writing Shorts video to: {output_video_path}")
        final_clip.write_videofile(
            output_video_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            preset="fast",
            threads=os.cpu_count() or 1,
            logger=None # moviepy 로그를 직접 처리하지 않음
        )
        logger.info(f"Video successfully converted to Shorts and saved to {output_video_path}")
        return True

    except Exception as e:
        logger.error(f"Error converting video to Shorts: {e}", exc_info=True)
        return False

# 테스트용 코드
if __name__ == "__main__":
    from src.config import setup_logging
    setup_logging()

    # 테스트를 위한 더미 영상 파일 생성 (실제 moviepy가 동작하려면 유효한 영상 파일이어야 합니다)
    # 작은 mp4 파일을 로컬에 준비하거나, dummy_video.mp4로 이름을 변경하여 사용하세요.
    # 예시: ffmpeg -f lavfi -i color=c=blue:s=1280x720:d=10 -f lavfi -i sine=frequency=1000:duration=10 -c:v libx264 -c:a aac -strict experimental -pix_fmt yuv420p dummy_video.mp4
    
    input_test_video = "dummy_video.mp4" # 여기에 실제 테스트 영상 파일 경로를 지정하세요.
    output_test_shorts = "output/test_shorts_output.mp4"
    font_test_path = "fonts/Catfont.ttf"

    if not os.path.exists(input_test_video):
        print(f"Error: Test video file not found at '{input_test_video}'. Please create one or specify a valid path.")
        # 작은 테스트 영상 다운로드 예시 (유효한 링크 필요)
        # import requests
        # test_video_url = "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4"
        # print(f"Downloading sample video from {test_video_url}...")
        # try:
        #     r = requests.get(test_video_url, stream=True)
        #     r.raise_for_status()
        #     with open(input_test_video, 'wb') as f:
        #         for chunk in r.iter_content(chunk_size=8192):
        #             f.write(chunk)
        #     print("Sample video downloaded.")
        # except Exception as e:
        #     print(f"Failed to download sample video: {e}")
        #     sys.exit(1)

    print(f"Attempting to convert '{input_test_video}' to Shorts...")
    if convert_to_shorts(input_test_video, output_test_shorts, font_path=font_test_path):
        print(f"Successfully converted to Shorts: {output_test_shorts}")
    else:
        print("Failed to convert video to Shorts.")
