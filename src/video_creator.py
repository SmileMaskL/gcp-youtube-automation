"""
영상 생성 모듈 (최종 완성본)
"""
import subprocess
from pathlib import Path
import logging
from .config import Config

logger = logging.getLogger(__name__)

def create_video_with_subtitles(
    background_video_path: str,
    audio_path: str,
    script_with_timing: list,
    output_path: str
):
    """자막이 포함된 최종 영상 생성"""
    try:
        # FFmpeg 명령어 구성
        cmd = [
            "ffmpeg",
            "-y",  # 덮어쓰기 허용
            "-i", str(background_video_path),
            "-i", str(audio_path),
            "-vf", f"scale={Config.SHORTS_WIDTH}:{Config.SHORTS_HEIGHT}:force_original_aspect_ratio=decrease,pad={Config.SHORTS_WIDTH}:{Config.SHORTS_HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            str(output_path)
        ]
        
        logger.info(f"영상 생성 명령어: {' '.join(cmd)}")
        
        # 영상 생성 실행
        subprocess.run(cmd, check=True)
        logger.info(f"영상 생성 완료: {output_path}")
        
        return output_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"영상 생성 실패 (FFmpeg 오류): {e}")
        raise
    except Exception as e:
        logger.error(f"영상 생성 중 오류 발생: {e}")
        raise
