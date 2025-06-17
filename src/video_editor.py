import os
import logging
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
from moviepy.video.fx.all import resize

logger = logging.getLogger(__name__)

def create_video(bg_video_path: str, audio_path: str, output_path: str) -> str:
    """
    배경 영상과 오디오를 결합하여 최종 영상 생성
    
    Args:
        bg_video_path: 배경 영상 파일 경로
        audio_path: 오디오 파일 경로
        output_path: 출력 파일 경로
        
    Returns:
        생성된 영상 파일 경로
    """
    try:
        # 배경 영상 로드 (최대 60초로 제한)
        video_clip = VideoFileClip(bg_video_path).subclip(0, 60)
        
        # 오디오 클립 로드
        audio_clip = AudioFileClip(audio_path)
        
        # 영상 길이를 오디오 길이에 맞추기
        if video_clip.duration < audio_clip.duration:
            # 영상이 오디오보다 짧으면 영상 반복
            video_clip = video_clip.loop(duration=audio_clip.duration)
        else:
            # 영상이 오디오보다 길면 오디오 길이에 맞춰 자르기
            video_clip = video_clip.subclip(0, audio_clip.duration)
        
        # 영상과 오디오 결합
        final_clip = video_clip.set_audio(audio_clip)
        
        # 해상도 조정 (1080x1920 - 쇼츠 형식)
        final_clip = final_clip.fx(resize, width=1080)
        if final_clip.h < 1920:
            final_clip = final_clip.fx(resize, height=1920)
        
        # 영상 저장
        final_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            fps=30,
            preset="fast"
        )
        
        logger.info(f"영상 생성 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"영상 생성 실패: {e}")
        raise
    finally:
        # 클립 객체 닫기
        if 'video_clip' in locals():
            video_clip.close()
        if 'audio_clip' in locals():
            audio_clip.close()
        if 'final_clip' in locals():
            final_clip.close()
