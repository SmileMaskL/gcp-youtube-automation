"""
최종 비디오 생성 모듈
- 역할: utils의 도구들을 사용하여 오디오, 비디오, 텍스트를 하나로 합치는 작업장
"""

import os
import uuid
import logging
from pathlib import Path
from moviepy.editor import *

# 이제 'utils'에서 필요한 도구들을 안전하게 가져옵니다.
from utils import text_to_speech, download_video_from_pexels

logger = logging.getLogger(__name__)

def create_final_video(topic: str, title: str, script: str) -> str:
    """
    하나의 완성된 쇼츠 비디오를 생성하는 전체 프로세스
    """
    logger.info(f"🎬 '{topic}' 주제의 영상 제작을 시작합니다.")
    video_path = None
    audio_path = None
    try:
        # 임시 파일들을 저장할 고유 디렉토리 생성
        temp_dir = Path(f"temp/{uuid.uuid4()}")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 음성 생성 (대본 기반)
        audio_path = temp_dir / "audio.mp3"
        text_to_speech(script, str(audio_path))
        
        # 2. 배경 영상 다운로드 (주제 기반)
        video_path = download_video_from_pexels(topic)

        # 3. 영상과 오디오 클립 로드
        audio_clip = AudioFileClip(str(audio_path))
        video_clip = VideoFileClip(video_path).without_audio()

        # 4. 영상 길이를 오디오 길이에 맞춤 (루프 또는 자르기)
        if video_clip.duration < audio_clip.duration:
            video_clip = video_clip.loop(duration=audio_clip.duration)
        else:
            video_clip = video_clip.subclip(0, audio_clip.duration)

        # 5. 영상에 오디오 합치기
        final_clip = video_clip.set_audio(audio_clip)

        # 6. 시선을 사로잡는 자막(타이틀) 추가
        txt_clip = TextClip(
            title,  # 영상에는 제목을 크게 보여줘서 클릭률을 높임
            fontsize=80,
            color='white',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=3,
            method='caption',
            size=(video_clip.w * 0.9, None)
        ).set_position('center').set_duration(final_clip.duration)

        # 7. 모든 요소를 최종 합성
        result_clip = CompositeVideoClip([final_clip, txt_clip])
        
        # 8. 최종 결과물 파일로 저장
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{topic.replace(' ', '_')}_{uuid.uuid4()}.mp4"
        
        result_clip.write_videofile(str(output_path), codec='libx264', audio_codec='aac', temp_audiofile=str(temp_dir / 'temp-audio.m4a'), remove_temp=True, logger=None)
        
        logger.info(f"✅ 영상 제작 완료: {output_path}")
        return str(output_path)

    except Exception as e:
        logger.error(f"영상 제작 중 심각한 오류 발생: {e}", exc_info=True)
        return None
    finally:
        # 작업이 끝나면 다운로드한 비디오 소스 정리
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except OSError:
                pass # 가끔 파일 사용 중이라 삭제 안될 때 대비
