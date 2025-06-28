# src/video_generator.py
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # 모듈별 로거 사용 권장
logger.setLevel(logging.INFO)

def create_video_from_images_and_audio(image_paths, audio_path, output_video_path):
    """
    여러 이미지와 오디오 파일을 합쳐 비디오를 생성합니다.
    쇼츠는 세로형(9:16 비율)에 최적화됩니다.
    :param image_paths: 사용할 이미지 파일 경로 리스트 (JPEG, PNG 등)
    :param audio_path: 배경 오디오 파일 경로 (MP3 등)
    :param output_video_path: 출력 비디오 파일 경로 (MP4)
    """
    logger.info(f"비디오 생성 시작. 이미지: {len(image_paths)}개, 오디오: {audio_path}")

    if not image_paths:
        logger.error("이미지 경로 목록이 비어있어 비디오를 생성할 수 없습니다.")
        raise ValueError("비디오 생성을 위한 이미지가 없습니다.")
    
    audio_clip = None
    img_clip = None
    final_video_clip = None

    try:
        # 오디오 파일 로드하여 비디오 길이 결정
        audio_clip = AudioFileClip(audio_path)
        video_duration = audio_clip.duration
        logger.info(f"오디오 길이: {video_duration:.2f}초")

        # 각 이미지 클립 생성
        clips = []
        # 이미지당 지속 시간 = 전체 오디오 길이 / 이미지 개수
        # 단, 이미지당 최소 1초 이상은 보여지도록 조정
        img_duration_per_clip = max(1, video_duration / len(image_paths))

        for img_path in image_paths:
            img_clip = ImageClip(img_path)
            
            # 원본 이미지 비율 계산
            original_width, original_height = img_clip.size
            target_aspect_ratio = 1080 / 1920 # 9:16 세로형 비율

            if original_width / original_height > target_aspect_ratio:
                # 이미지가 너무 넓은 경우 (가로가 더 김), 세로 중앙 기준으로 가로를 자름
                new_width = int(original_height * target_aspect_ratio)
                x_center = original_width / 2
                img_clip = img_clip.crop(x_center=x_center, width=new_width)
            else:
                # 이미지가 너무 긴 경우 (세로가 더 김), 가로 중앙 기준으로 세로를 자름
                new_height = int(original_width / target_aspect_ratio)
                y_center = original_height / 2
                img_clip = img_clip.crop(y_center=y_center, height=new_height)

            # 최종 비디오 해상도에 맞게 리사이즈
            img_clip = img_clip.resize(newsize=(1080, 1920))
            
            # 각 이미지 클립의 지속 시간 설정
            clips.append(img_clip.set_duration(img_duration_per_clip))

        # 모든 이미지 클립 연결
        final_video_clip = concatenate_videoclips(clips, method="compose") # compose는 해상도 유지

        # 최종 비디오 클립의 길이를 오디오 길이와 정확히 일치시킵니다.
        if final_video_clip.duration > video_duration:
            final_video_clip = final_video_clip.subclip(0, video_duration)
        else:
            logger.warning("비디오 길이가 오디오 길이보다 짧습니다. 마지막 이미지를 늘립니다.")
            final_video_clip = final_video_clip.set_duration(video_duration)


        # 오디오를 비디오에 추가
        final_video_clip = final_video_clip.set_audio(audio_clip)

        # 결과 비디오 파일 저장 (최대 60초)
        final_video_clip.write_videofile(
            output_video_path,
            fps=24, # 프레임 속도 (YouTube Shorts 권장 24~30fps)
            codec="libx264",
            audio_codec="aac",
            preset="medium", # 인코딩 속도 vs 파일 크기 (medium은 균형)
            threads=4, # 인코딩 스레드 수 (CPU 사용량에 따라 조절)
            logger=None # MoviePy 로그를 표시하지 않음
        )
        logger.info(f"비디오 생성 완료 및 저장: {output_video_path}")
        
    except Exception as e:
        logger.error(f"비디오 생성 중 오류 발생: {e}")
        raise
    finally:
        # 사용된 클립 메모리 해제 (항상 실행)
        if audio_clip:
            audio_clip.close()
        # img_clip은 clips 리스트에 포함되어 있으므로 개별 close 불필요
        if final_video_clip:
            final_video_clip.close()


if __name__ == '__main__':
    # 로컬 테스트용 더미 파일 생성
    # 테스트를 위해 dummy_images 폴더에 test_image1.jpg, test_image2.jpg 등을 넣어두세요.
    # dummy_audio.mp3 파일도 필요합니다.
    dummy_image_dir = "dummy_images"
    dummy_audio_file = "dummy_audio.mp3"
    output_test_video = "test_output_shorts.mp4"

    if not os.path.exists(dummy_image_dir) or not os.path.exists(dummy_audio_file):
        print("테스트를 위해 'dummy_images' 폴더와 'dummy_audio.mp3' 파일이 필요합니다.")
        print("dummy_images 폴더에 이미지 파일을 몇 개 넣어주세요.")
        print("Eleven Labs로 짧은 오디오 파일을 만들어서 'dummy_audio.mp3'로 저장해주세요.")
    else:
        # 더미 이미지 경로 목록 생성
        dummy_image_paths = [os.path.join(dummy_image_dir, f) for f in os.listdir(dummy_image_dir) if f.endswith(('.jpg', '.png'))]
        dummy_image_paths.sort() # 순서대로 처리되도록 정렬 (선택 사항)

        if not dummy_image_paths:
            print(f"'{dummy_image_dir}' 폴더에 이미지 파일이 없습니다.")
        else:
            try:
                print(f"더미 이미지: {dummy_image_paths}")
                print(f"더미 오디오: {dummy_audio_file}")
                create_video_from_images_and_audio(dummy_image_paths, dummy_audio_file, output_test_video)
                print(f"테스트 비디오 '{output_test_video}'가 성공적으로 생성되었습니다.")
            except Exception as e:
                print(f"테스트 비디오 생성 중 오류 발생: {e}")
