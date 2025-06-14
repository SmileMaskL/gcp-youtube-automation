# src/main.py
# 이 파일은 utils.py에 있는 도구들을 순서대로 조립해서 최종 결과물을 만드는 공장장 역할을 합니다.

import os
import logging
import uuid
from pathlib import Path
from utils import (
    generate_viral_content,
    text_to_speech,
    download_video_from_pexels,
    Config,
    logger
)
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip

# 배경 영상, 음성, 자막을 합쳐 최종 쇼츠 영상을 완성하는 함수입니다.
def create_final_video(script_text: str, bg_video_path: str, audio_path: str) -> str:
    try:
        logger.info("최종 영상 제작을 시작합니다.")
        
        audio_clip = AudioFileClip(audio_path)
        video_clip = VideoFileClip(bg_video_path)
        video_duration = audio_clip.duration
        
        # 배경 영상을 쇼츠 비율(9:16)에 맞게 자릅니다.
        w, h = video_clip.size
        target_ratio = 9 / 16
        if w / h > target_ratio:
            new_w = h * target_ratio
            video_clip = video_clip.crop(x_center=w/2, width=new_w)
        else:
            new_h = w / target_ratio
            video_clip = video_clip.crop(y_center=h/2, height=new_h)
            
        video_clip = video_clip.resize(height=Config.SHORTS_HEIGHT).set_duration(video_duration)
        
        # 보기 좋은 자막을 생성합니다.
        # 혹시 한글 폰트가 없어서 오류가 날 경우를 대비해, 기본 폰트를 사용하도록 예외처리를 추가했습니다.
        try:
            font_path = 'NanumGothic-Bold'
            TextClip("test", font=font_path) # 폰트가 있는지 테스트
        except Exception:
            logger.warning("NanumGothic-Bold 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
            font_path = 'Malgun Gothic' # Windows 기본 폰트
        
        txt_clip = TextClip(
            script_text,
            fontsize=70,
            color='white',
            font=font_path,
            stroke_color='black',
            stroke_width=2,
            size=(Config.SHORTS_WIDTH * 0.8, None),
            method='caption'
        ).set_position('center').set_duration(video_duration)
        
        # 모든 재료(영상, 소리, 자막)를 하나로 합칩니다.
        final_clip = CompositeVideoClip([video_clip, txt_clip]).set_audio(audio_clip)
        
        # 완성된 영상을 파일로 저장합니다.
        safe_title = "".join(c for c in script_text[:20] if c.isalnum()).rstrip()
        output_filename = f"{safe_title}_{uuid.uuid4()}.mp4"
        output_path = str(Config.OUTPUT_DIR / output_filename)
        
        final_clip.write_videofile(
            output_path, 
            fps=30, 
            codec='libx264',
            audio_codec='aac',
            threads=os.cpu_count() or 1,
            logger=None
        )
        logger.info(f"최종 영상 제작 성공: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"최종 영상 제작 중 심각한 오류 발생: {e}", exc_info=True)
        return ""

# 전체 자동화 시스템을 순서대로 실행하는 메인 함수입니다.
def main():
    logger.info("=" * 50)
    logger.info("💰💰 유튜브 수익형 자동화 시스템 V4 (완결판) 시작 💰💰")
    logger.info("=" * 50)
    
    Config.ensure_directories()
    
    # 1단계: AI에게 영상 주제를 주고 대본 받아오기
    topic = "부자가 되는 사소한 습관" # <-- 여기 주제만 자유롭게 바꾸세요!
    logger.info(f"🔥 오늘의 주제: {topic}")
    content = generate_viral_content(topic)
    
    # 2단계: AI가 써준 대본을 목소리로 바꾸기
    audio_filename = str(Config.TEMP_DIR / f"{uuid.uuid4()}.mp3")
    audio_path = text_to_speech(content['script'], audio_filename)
    
    # 3단계: 주제에 맞는 배경 영상 다운로드 받기
    audio_clip = AudioFileClip(audio_path)
    estimated_duration = audio_clip.duration + 1
    audio_clip.close()
    video_path = download_video_from_pexels(topic, duration=estimated_duration)
    
    # 4단계: 모든 재료(영상, 소리, 자막)를 합쳐서 최종 영상 만들기
    final_video_path = create_final_video(content['script'], video_path, audio_path)
    
    logger.info("=" * 50)
    if final_video_path:
        logger.info(f"✅ 모든 작업 완료! 최종 영상 경로: {final_video_path}")
    else:
        logger.error("❌ 최종 영상 생성에 실패했습니다.")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
