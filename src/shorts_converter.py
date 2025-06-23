# src/shorts_converter.py
import logging
import os
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

logger = logging.getLogger(__name__)


class ShortsConverter:
    def __init__(self):
        logger.info("ShortsConverter initialized.")

    def convert_to_shorts_format(self, input_video_path, output_video_path,
                                target_resolution=(1080, 1920), max_duration=60):
        """
        Converts an input video to YouTube Shorts vertical format (9:16 aspect ratio).
        """
        try:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.info(f"Converting video '{input_video_path}' to Shorts format. "
                        f"Target resolution: {target_resolution}, Max duration: {max_duration}s")

            clip = VideoFileClip(input_video_path)

            if clip.duration > max_duration:
                clip = clip.subclip(0, max_duration)
                logger.info(f"Video trimmed to {max_duration} seconds.")

            original_width, original_height = clip.size
            target_width, target_height = target_resolution

            if original_width * target_height > original_height * target_width:
                clip = clip.resize(height=target_height)
                current_width = clip.w
                x_center = current_width / 2
                clip = clip.crop(x_center - target_width / 2, 0,
                                 x_center + target_width / 2, target_height)
                logger.info("Video resized by height and cropped to target aspect ratio.")
            else:
                clip = clip.resize(width=target_width)
                current_height = clip.h
                y_center = current_height / 2
                clip = clip.crop(0, y_center - target_height / 2,
                                 target_width, y_center + target_height / 2)
                logger.info("Video resized by width and cropped to target aspect ratio.")

            clip.write_videofile(
                output_video_path,
                codec="libx264",
                audio_codec="aac",
                fps=24,
                temp_audiofile=f"{os.path.splitext(output_video_path)[0]}_temp_audio.m4a",
                remove_temp=True,
                logger=None
            )
            logger.info(f"Video converted successfully to: {output_video_path}")
            return output_video_path

        except Exception as e:
            logger.error(f"Error converting video to Shorts format: {e}", exc_info=True)
            raise

    def add_background_music(self, video_path, music_path, output_path, volume_ratio=0.3):
        """
        Adds background music to a video.
        """
        try:
            logger.info(f"Adding background music to '{video_path}' from '{music_path}'")
            video_clip = VideoFileClip(video_path)
            music_clip = AudioFileClip(music_path).set_duration(video_clip.duration)

            music_clip = music_clip.audio_fadein(1).audio_fadeout(1)

            final_audio = CompositeAudioClip([video_clip.audio, music_clip.volumex(volume_ratio)])
            final_clip = video_clip.set_audio(final_audio)

            final_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                fps=video_clip.fps,
                # E501 해결: 줄 길이를 79자 이하로 맞춤
                temp_audiofile=(f"{os.path.splitext(output_path)[0]}_music_temp_audio.m4a"),
                remove_temp=True,
                logger=None
            )
            logger.info(f"Background music added to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error adding background music: {e}", exc_info=True)
            raise
    
