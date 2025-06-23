# src/video_editor.py

import logging
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import os

logger = logging.getLogger(__name__)


def edit_video_for_shorts(video_path, content_text, video_title):
    """
    생성된 비디오에 자막, 제목 오버레이 등의 편집을 추가합니다.
    """
    try:
        logger.info(f"영상 편집 시작: {video_path}")

        clip = VideoFileClip(video_path)
        duration = clip.duration
        width, height = clip.size

        title_text_clip = TextClip(
            txt=video_title,
            fontsize=70,
            color='white',
            font='NanumSquare',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(width * 0.8, None)
        )
        title_text_clip = title_text_clip.set_pos(('center', 'top')).set_duration(duration)

        content_subtitle_clip = TextClip(
            txt=content_text,
            fontsize=50,
            color='yellow',
            font='NanumSquare',
            stroke_color='black',
            stroke_width=1.5,
            method='caption',
            size=(width * 0.9, None)
        ).set_pos(('center', 'bottom')).set_duration(duration)

        final_clip_edited = CompositeVideoClip([
            clip,
            title_text_clip,
            content_subtitle_clip
        ])

        final_clip_edited.write_videofile(
            video_path,
            codec="libx264",
            audio_codec="aac",
            fps=clip.fps,
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            temp_audiofile=f"{os.path.splitext(video_path)[0]}_edited_audio.m4a",
            remove_temp=True,
            logger=None
        )

        logger.info(f"영상 편집 완료: {video_path}")
        return video_path

    except Exception as e:
        logger.error(f"비디오 편집 중 오류 발생: {e}", exc_info=True)
        raise
    
