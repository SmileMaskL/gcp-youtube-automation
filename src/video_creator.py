import os
from moviepy.editor import *
from utils import text_to_speech, add_text_to_clip, download_video_from_pexels
from openai_utils import split_script
import uuid
import tempfile
import logging

logger = logging.getLogger(__name__)

def create_video(script, topic):
    logger.info("📽️ 영상 생성 시작...")

    # 배경 영상 다운로드
    background_video = download_video_from_pexels(topic)
    if not background_video:
        logger.error("❌ 배경 영상 다운로드 실패")
        return None

    # 대본 분할
    sentences = split_script(script)
    if not sentences:
        logger.warning("⚠️ 대본이 비어 있음")
        return None

    # 오디오 생성 및 영상 조합
    clips = []
    for idx, sentence in enumerate(sentences):
        logger.info(f"🎤 음성 생성 중: {sentence}")
        audio_path = text_to_speech(sentence)

        if not audio_path or not os.path.exists(audio_path):
            logger.warning("⚠️ 음성 생성 실패, 스킵")
            continue

        video = VideoFileClip(background_video).subclip(0, AudioFileClip(audio_path).duration)
        video = video.set_audio(AudioFileClip(audio_path))
        video = add_text_to_clip(video.filename, sentence, "temp_text.mp4")  # 수정된 부분
        clips.append(video)

    if not clips:
        logger.error("❌ 클립 없음. 영상 생성 실패")
        return None

    final_clip = concatenate_videoclips(clips, method="compose")
    output_path = os.path.join("output", f"{uuid.uuid4()}.mp4")
    os.makedirs("output", exist_ok=True)
    final_clip.write_videofile(output_path, fps=24)

    logger.info(f"✅ 영상 생성 완료: {output_path}")
    return output_path
