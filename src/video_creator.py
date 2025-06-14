"""
최종 비디오 생성 모듈 (2025년 최신 버전)
- 역할: 오디오, 비디오, 텍스트를 합쳐 최종 YouTube Shorts 영상 생성
"""

import os
import uuid
import logging
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.config import change_settings
from utils import text_to_speech, download_video_from_pexels, create_default_audio

# ImageMagick 경로 설정 (필수)
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

logger = logging.getLogger(__name__)

def create_final_video(topic: str, title: str, script: str) -> str:
    """
    최종 YouTube Shorts 영상 생성
    Args:
        topic: 영상 주제 (str)
        title: 영상 제목 (str)
        script: 영상 대본 (str)
    Returns:
        생성된 영상 파일 경로 (str)
    """
    logger.info(f"🎬 '{topic}' 주제의 영상 제작을 시작합니다.")
    
    # 임시 파일 저장 폴더
    temp_dir = Path(f"temp/{uuid.uuid4()}")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. 음성 파일 생성 (ElevenLabs 실패 시 gTTS로 대체)
        audio_path = temp_dir / "audio.mp3"
        try:
            text_to_speech(script, str(audio_path))
        except Exception as e:
            logger.error(f"음성 생성 실패, 기본 음성 사용: {e}")
            create_default_audio(script, str(audio_path))

        # 2. 배경 영상 다운로드 (Pexels 실패 시 기본 영상 생성)
        video_path = None
        try:
            video_path = download_video_from_pexels(topic)
            video_clip = VideoFileClip(video_path).without_audio()
        except Exception as e:
            logger.error(f"배경 영상 다운로드 실패, 기본 영상 사용: {e}")
            video_clip = ColorClip(size=(1080, 1920), color=(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100)), duration=60)

        # 3. 오디오 클립 로드
        audio_clip = AudioFileClip(str(audio_path))

        # 4. 영상 길이 조정 (오디오 길이에 맞춤)
        if video_clip.duration < audio_clip.duration:
            video_clip = video_clip.loop(duration=audio_clip.duration)
        else:
            video_clip = video_clip.subclip(0, audio_clip.duration)

        # 5. 자막 생성 (고양이 폰트 사용 시도)
        try:
            txt_clip = TextClip(
                title,
                fontsize=80,
                color='white',
                font='fonts/Catfont.ttf',
                stroke_color='black',
                stroke_width=3,
                size=(video_clip.w * 0.9, None),
                method='caption'
            )
        except:
            txt_clip = TextClip(
                title,
                fontsize=80,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=3,
                size=(video_clip.w * 0.9, None),
                method='caption'
            )
        
        txt_clip = txt_clip.set_position('center').set_duration(audio_clip.duration)

        # 6. 최종 영상 합성
        final_clip = CompositeVideoClip([video_clip.set_audio(audio_clip), txt_clip])

        # 7. 출력 폴더 생성
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{topic.replace(' ', '_')}_{uuid.uuid4()}.mp4"

        # 8. 영상 저장 (고화질 설정)
        final_clip.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            bitrate="8000k",
            fps=30,
            threads=4,
            preset='slow',
            logger=None
        )

        logger.info(f"✅ 영상 제작 완료: {output_path}")
        return str(output_path)

    except Exception as e:
        logger.error(f"❌ 영상 제작 중 심각한 오류 발생: {e}", exc_info=True)
        return None

    finally:
        # 임시 파일 정리
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except:
                pass
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass