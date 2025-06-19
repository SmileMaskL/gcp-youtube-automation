from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip
import os
from pathlib import Path
from src.config import VIDEO_DIR
from src.monitoring import log_system_health

def create_video(audio_path, background_image_path, output_filename="final_video.mp4"):
    """
    오디오 파일과 배경 이미지를 결합하여 Shorts에 적합한 9:16 비율의 비디오를 생성합니다.
    """
    output_path = os.path.join(VIDEO_DIR, output_filename)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        audio_clip = AudioFileClip(audio_path)
        video_duration = audio_clip.duration

        # 배경 이미지 로드
        image_clip = ImageClip(background_image_path)

        # Shorts (9:16 비율)에 맞게 비디오 크기 설정 (예: 1080x1920)
        target_width = 1080
        target_height = 1920

        # 이미지 비율 유지하면서 목표 크기에 맞게 조정 (fill mode)
        # 이미지 원본 비율이 16:9라고 가정하고, 9:16으로 잘라낼 영역을 계산합니다.
        img_width, img_height = image_clip.size

        # 원본 이미지의 가로/세로 비율
        img_aspect_ratio = img_width / img_height
        # 목표 비디오의 가로/세로 비율
        video_aspect_ratio = target_width / target_height # 9/16 = 0.5625

        if img_aspect_ratio > video_aspect_ratio:
            # 이미지가 더 넓은 경우 (가로형 이미지), 높이를 기준으로 폭을 잘라냅니다.
            new_width = int(img_height * video_aspect_ratio)
            new_height = img_height
            x_center = img_width / 2
            y_center = img_height / 2
            image_clip = image_clip.crop(x1=x_center - new_width / 2,
                                        y1=y_center - new_height / 2,
                                        x2=x_center + new_width / 2,
                                        y2=y_center + new_height / 2)
        else:
            # 이미지가 더 좁은 경우 (세로형 이미지 또는 정사각형), 폭을 기준으로 높이를 잘라냅니다.
            new_width = img_width
            new_height = int(img_width / video_aspect_ratio)
            x_center = img_width / 2
            y_center = img_height / 2
            image_clip = image_clip.crop(x1=x_center - new_width / 2,
                                        y1=y_center - new_height / 2,
                                        x2=x_center + new_width / 2,
                                        y2=y_center + new_height / 2)

        # 최종적으로 목표 해상도로 리사이징
        image_clip = image_clip.resize((target_width, target_height))

        # 비디오 클립 생성 (배경 이미지를 비디오 길이만큼 늘림)
        video_clip = image_clip.set_duration(video_duration)
        video_clip = video_clip.set_audio(audio_clip)

        # 최종 비디오 저장
        video_clip.write_videofile(output_path, 
                                   codec='libx264', 
                                   audio_codec='aac', 
                                   fps=24, # 프레임 속도 설정 (24 또는 30)
                                   temp_audiofile=os.path.join(output_path.parent, "temp_audio.m4a"), # 임시 오디오 파일 경로
                                   remove_temp=True
                                )

        audio_clip.close()
        image_clip.close()
        video_clip.close()

        log_system_health(f"비디오가 성공적으로 생성되었습니다: {output_path}", level="info")
        return output_path
    except Exception as e:
        log_system_health(f"비디오 생성 중 오류 발생: {e}", level="error")
        raise ValueError(f"비디오 생성 실패: {e}")

# For local testing (optional)
if __name__ == "__main__":
    # 테스트를 위해 dummy audio.mp3와 background.jpg 파일을 준비해야 합니다.
    # 예시: 임시 파일 생성
    dummy_audio_path = "output/audio/dummy_audio.mp3"
    dummy_bg_path = "output/backgrounds/dummy_bg.jpg"

    # 임시 오디오 파일 생성 (10초 길이)
    # from moviepy.audio.AudioClip import AudioArrayClip
    # import numpy as np
    # sample_rate = 44100
    # duration = 10 # seconds
    # t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # data = np.sin(2 * np.pi * 440 * t) * 0.5 # 440 Hz sine wave
    # audio_data = np.array([data, data]).T # Stereo
    # audio_clip_temp = AudioArrayClip(audio_data, fps=sample_rate)
    # Path(dummy_audio_path).parent.mkdir(parents=True, exist_ok=True)
    # audio_clip_temp.write_audiofile(dummy_audio_path)
    # audio_clip_temp.close()

    # 임시 배경 이미지 생성 (1280x720)
    # from PIL import Image
    # dummy_img = Image.new('RGB', (1280, 720), color = (73, 109, 137))
    # Path(dummy_bg_path).parent.mkdir(parents=True, exist_ok=True)
    # dummy_img.save(dummy_bg_path)

    try:
        # 실제 테스트 시 위 주석 처리된 부분을 참고하여 dummy 파일 생성 후 실행
        # 또는 실제 오디오/이미지 파일 경로를 지정
        # video_path = create_video(dummy_audio_path, dummy_bg_path, "test_video.mp4")
        # print(f"Test video saved to: {video_path}")
        print("To run this test, please manually create dummy audio.mp3 and background.jpg files in their respective directories.")
    except ValueError as e:
        print(f"Error during test: {e}")
