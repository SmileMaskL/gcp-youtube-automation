# src/video_generator.py

import logging
import os
import requests
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, TextClip
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def create_video_from_images_and_audio(images, audio_path, output_path):
    """
    단일 이미지 → 오디오 길이만큼 동영상 생성
    """
    try:
        audio = AudioFileClip(audio_path)
        duration = audio.duration

        clip = ImageClip(images[0]).set_duration(duration).set_audio(audio)
        clip = clip.resize(height=1920).crop(x_center=clip.w/2, width=1080, height=1920)
        clip.write_videofile(output_path, fps=30)
        logger.info(f"✅ Video saved to '{output_path}'")
    except Exception as e:
        logger.error(f"❌ Video 생성 실패: {e}")
        raise

def download_image(url):
    """
    이미지 URL을 다운로드해 로컬 임시 파일로 저장 후 경로 반환
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        tmp_file = NamedTemporaryFile(delete=False, suffix=".png")
        for chunk in response.iter_content(1024):
            tmp_file.write(chunk)
        tmp_file.close()
        logger.info(f"Downloaded image: {url} -> {tmp_file.name}")
        return tmp_file.name
    except Exception as e:
        logger.error(f"Failed to download image: {url}, error: {e}")
        raise

def generate_video_from_script(script_path, images, output_path):
    """
    script_path: 저장된 대본 파일 경로
    images: [url1, url2, ...]
    output_path: 최종 mp4 경로

    - script 첫 줄을 TextClip으로 생성 (3초)
    - images는 각각 3초 duration으로 ImageClip 생성
    - 최종적으로 concatenate 후 output_path로 저장
    """
    clips = []
    temp_files = []

    try:
        # 스크립트 첫 줄 텍스트 클립 생성
        with open(script_path, "r", encoding="utf-8") as f:
            script_lines = f.readlines()

        if script_lines:
            txt_clip = TextClip(
                script_lines[0].strip(),
                fontsize=70,
                color='white',
                bg_color='black',
                size=(1080,1920),
                method='caption'
            ).set_duration(3)
            clips.append(txt_clip)
            logger.info(f"Added TextClip with script first line.")

        # 이미지 URL을 로컬 파일로 다운로드 후 ImageClip 생성
        for img_url in images:
            local_img = download_image(img_url)
            temp_files.append(local_img)

            img_clip = ImageClip(local_img).set_duration(3).resize(height=1920).set_position("center")
            clips.append(img_clip)
            logger.info(f"Added ImageClip: {img_url}")

        if not clips:
            raise ValueError("No clips generated. Check script or images input.")

        # concatenate and export
        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(output_path, fps=24)
        logger.info(f"✅ Final video saved to '{output_path}'")

    except Exception as e:
        logger.error(f"❌ generate_video_from_script 실패: {e}")
        raise

    finally:
        # 임시 다운로드 파일 삭제
        for tmp in temp_files:
            try:
                os.remove(tmp)
                logger.info(f"Deleted temp file: {tmp}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file {tmp}: {e}")
