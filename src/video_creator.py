# src/video_creator.py

import logging
import os
from moviepy.editor import VideoFileClip, AudioFileClip # F401 CompositeAudioClip, concatenate_audioclips, CompositeVideoClip 제거

logger = logging.getLogger(__name__)


def create_short_video(background_video_path, audio_file_path, output_video_path):
    """
    배경 영상과 음성 파일을 결합하여 최종 쇼츠 비디오를 생성합니다.
    """
    try:
        logger.info("영상 제작 시작.")

        background_clip = VideoFileClip(background_video_path)
        logger.info(f"배경 영상 로드 완료. 길이: {background_clip.duration:.2f}초")

        audio_clip = AudioFileClip(audio_file_path)
        logger.info(f"오디오 파일 로드 완료. 길이: {audio_clip.duration:.2f}초")

        final_duration = min(background_clip.duration, audio_clip.duration, 60)

        if audio_clip.duration > background_clip.duration:
            background_clip = background_clip.loop(duration=audio_clip.duration)
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.info(f"배경 영상이 오디오 길이({audio_clip.duration:.2f}초)에 맞춰 루프됩니다.")

        background_clip = background_clip.subclip(0, final_duration)
        audio_clip = audio_clip.subclip(0, final_duration)

        final_clip = background_clip.set_audio(audio_clip)

        target_width = 1080
        target_height = 1920

        if final_clip.w * target_height > final_clip.h * target_width:
            final_clip = final_clip.resize(height=target_height)
            x_center = final_clip.w / 2
            y_center = final_clip.h / 2
            final_clip = final_clip.crop(
                x_center - target_width / 2, y_center - target_height / 2,
                x_center + target_width / 2, y_center + target_height / 2
            )
        else:
            final_clip = final_clip.resize(width=target_width)
            x_center = final_clip.w / 2
            y_center = final_clip.h / 2
            final_clip = final_clip.crop(
                x_center - target_width / 2, y_center - target_height / 2,
                x_center + target_width / 2, y_center + target_height / 2
            )

        final_clip.write_videofile(
            output_video_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            temp_audiofile=f"{os.path.splitext(output_video_path)[0]}_audio.m4a",
            remove_temp=True,
            logger=None
        )
        logger.info(f"최종 비디오 생성 성공: {output_video_path}")
        return output_video_path

    except Exception as e:
        logger.error(f"비디오 생성 중 오류 발생: {e}", exc_info=True)
        raise
    
