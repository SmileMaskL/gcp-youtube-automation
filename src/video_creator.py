# src/video_creator.py
import logging
import os
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.config import change_settings # FFmpeg 경로 설정
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.editor import ImageClip
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# FFmpeg 경로 설정 (Cloud Functions 환경에 맞게)
# Cloud Functions 런타임에 기본 FFmpeg가 포함되어 있으므로, moviepy가 자동으로 찾을 수 있습니다.
# 만약 문제가 발생하면, Cloud Function에 custom FFmpeg를 포함시키거나,
# moviepy.config.change_settings({"FFMPEG_BINARY": "/path/to/ffmpeg"}) 등으로 설정 필요.
# 현재는 별도 설정 없이 진행합니다.

class VideoCreator:
    def __init__(self, font_path: str):
        self.font_path = font_path
        if not os.path.exists(self.font_path):
            logger.error(f"Font file not found at {self.font_path}. Video creation might fail or use default font.")
            # 폰트가 없으면 기본 폰트 사용 또는 에러 처리 로직 추가 필요
            # 현재는 에러 로그만 남기고 진행. main.py에서 폰트 다운로드 실패 시 중단하도록 처리됨.

    def create_video(self, audio_path: str, text_content: str, output_path: str, background_video_path: str = None) -> bool:
        """
        오디오와 텍스트를 기반으로 60초 길이의 Shorts 비디오를 생성합니다.
        
        Args:
            audio_path (str): 음성 파일 경로.
            text_content (str): 비디오에 표시할 텍스트 내용.
            output_path (str): 최종 비디오 저장 경로.
            background_video_path (str, optional): 배경 비디오 파일 경로 (없으면 단색 배경).

        Returns:
            bool: 비디오 생성 성공 여부.
        """
        try:
            audio_clip = AudioFileClip(audio_path)
            video_duration = min(audio_clip.duration, 60) # 최대 60초 Shorts

            # 배경 비디오 또는 단색 배경 생성
            if background_video_path and os.path.exists(background_video_path):
                # TODO: 비디오 다운로더 연동 필요
                # 현재는 배경 비디오 다운로드 로직이 없으므로 단색 배경으로 처리
                logger.warning("Background video path provided but not yet implemented. Using solid color background.")
                final_video = ColorClip((1080, 1920), color=(0, 0, 0), duration=video_duration) # Shorts 비율 9:16
            else:
                final_video = ColorClip((1080, 1920), color=(0, 0, 0), duration=video_duration) # Shorts 비율 9:16

            # 텍스트 클립 생성
            # text_content를 적절히 분할하여 한 화면에 너무 많은 텍스트가 표시되지 않도록 합니다.
            # 여기서는 간단하게 전체 텍스트를 사용하지만, 실제로는 문장 단위로 나누어 시간 동기화 필요
            
            # SubtitlesClip 대신 TextClip을 사용하여 직접 텍스트 오버레이
            text_clip = (TextClip(text_content, 
                                fontsize=60, 
                                color='white', 
                                font=self.font_path, # 고양이체 폰트 적용
                                method='caption', # 텍스트 자동 줄바꿈
                                stroke_color='black', 
                                stroke_width=2,
                                align='center',
                                size=(final_video.w * 0.8, None)) # 영상 너비의 80% 사용, 높이는 자동 조절
                        .set_duration(video_duration)
                        .set_position(('center', 'center')))

            # 오디오 클립을 영상에 설정
            final_video = final_video.set_audio(audio_clip.set_duration(video_duration))

            # 텍스트 클립을 비디오에 합성
            final_clip = CompositeVideoClip([final_video, text_clip])

            # 최종 비디오 저장
            logger.info(f"Writing final video to {output_path}...")
            final_clip.write_videofile(
                output_path, 
                fps=24, 
                codec="libx264", 
                audio_codec="aac",
                temp_audiofile=os.path.join(os.path.dirname(output_path), f"temp_audio_{uuid.uuid4().hex}.m4a"), # 임시 오디오 파일 경로 지정
                remove_temp=True
            )
            logger.info(f"Video successfully created at {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating video: {e}", exc_info=True)
            return False

# 필요한 경우, src/bg_downloader.py와 연동하여 배경 영상 다운로드 로직 추가 필요
# 현재는 배경 영상 다운로더가 구현되어 있지 않아 단색 배경으로 진행됩니다.
# 만약 배경 영상을 사용하려면 bg_downloader.py에서 Pexels API 등을 사용하여 영상을 다운로드하고,
# 해당 경로를 create_video 함수에 전달하도록 main.py를 수정해야 합니다.
