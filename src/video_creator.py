import os
import logging
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips, TextClip
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

logger = logging.getLogger(__name__)

def create_video(
    background_video_path: str,
    audio_path: str,
    output_video_path: str,
    font_path: str = "/app/fonts/Catfont.ttf", # Dockerfile에서 복사된 폰트 경로
    target_resolution=(1080, 1920) # YouTube Shorts 세로 비율 (9:16)
):
    """
    배경 영상과 음성을 결합하여 최종 영상을 생성합니다.
    Args:
        background_video_path (str): 배경 비디오 파일 경로.
        audio_path (str): 음성 파일 경로.
        output_video_path (str): 최종 비디오를 저장할 경로.
        font_path (str): 자막에 사용할 폰트 파일 경로 (고양이체.ttf).
        target_resolution (tuple): 최종 영상 해상도 (너비, 높이).
    """
    logger.info(f"Creating video: BG={background_video_path}, Audio={audio_path}, Output={output_video_path}")

    try:
        # 배경 비디오 로드
        bg_clip = VideoFileClip(background_video_path)
        logger.info(f"Background video loaded. Duration: {bg_clip.duration:.2f}s")

        # 오디오 클립 로드
        audio_clip = AudioFileClip(audio_path)
        logger.info(f"Audio clip loaded. Duration: {audio_clip.duration:.2f}s")

        # 오디오 길이에 맞춰 비디오 클립 자르기 또는 반복
        if audio_clip.duration < bg_clip.duration:
            bg_clip = bg_clip.subclip(0, audio_clip.duration)
            logger.info(f"Background video subclipped to audio duration: {bg_clip.duration:.2f}s")
        elif audio_clip.duration > bg_clip.duration:
            # 비디오가 오디오보다 짧으면, 비디오를 반복하여 오디오 길이에 맞춤
            num_repeats = int(audio_clip.duration / bg_clip.duration) + 1
            bg_clip = concatenate_videoclips([bg_clip] * num_repeats).subclip(0, audio_clip.duration)
            logger.info(f"Background video repeated to match audio duration: {bg_clip.duration:.2f}s")
        
        # 비디오 해상도 조정 (YouTube Shorts 권장 세로 비율 9:16)
        # 1080x1920 (FHD 세로)
        # 현재 비디오의 종횡비를 확인하고, 필요에 따라 크기 조정 또는 크롭
        current_aspect_ratio = bg_clip.w / bg_clip.h
        target_aspect_ratio = target_resolution[0] / target_resolution[1] # 1080/1920 = 0.5625

        if current_aspect_ratio != target_aspect_ratio:
            logger.info(f"Resizing/Cropping background video from {bg_clip.size} to {target_resolution} for Shorts format.")
            bg_clip = bg_clip.fx(vfx.resize, newsize=target_resolution) # 새 해상도로 강제 조정

        # 최종 영상의 오디오 설정 (배경 영상 오디오는 제거하고 새로운 음성 클립 사용)
        final_clip = bg_clip.set_audio(audio_clip)

        # 자막 추가 (선택 사항 - 스크립트를 기반으로)
        # 자막 생성 로직은 복잡하므로 여기서는 간단히 텍스트 오버레이 예시만
        # 실제 자막은 스크립트의 타임스탬프를 기반으로 해야 함
        # if script_text:
        #     # 스크립트 텍스트를 기반으로 자막 생성 로직 필요 (예: 음성-텍스트 동기화 라이브러리 사용)
        #     # 여기서는 간단히 영상 중앙에 고정 텍스트 오버레이 예시
        #     text_clip = TextClip("안녕하세요! 고양이체입니다.", fontsize=70, color='white', font=font_path,
        #                          method='caption', size=(final_clip.w*0.8, None))
        #     text_clip = text_clip.set_duration(final_clip.duration).set_pos('center')
        #     final_clip = CompositeVideoClip([final_clip, text_clip])

        # 출력 디렉토리 확인 및 생성
        output_dir = os.path.dirname(output_video_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 최종 영상 저장
        final_clip.write_videofile(
            output_video_path,
            codec="libx264", # 비디오 코덱
            audio_codec="aac", # 오디오 코덱
            fps=24, # 프레임 속도 (원본 유지 또는 24, 30 등)
            preset="medium", # 압축 설정 (파일 크기와 품질 조절)
            threads=os.cpu_count() or 2 # 사용 가능한 CPU 코어 수 활용
        )
        logger.info(f"Video successfully created and saved to {output_video_path}")

    except Exception as e:
        logger.error(f"Failed to create video: {e}", exc_info=True)
        raise
    finally:
        if 'bg_clip' in locals() and bg_clip:
            bg_clip.close()
        if 'audio_clip' in locals() and audio_clip:
            audio_clip.close()
        if 'final_clip' in locals() and final_clip:
            final_clip.close()
