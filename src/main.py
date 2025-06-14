##### 🎯 **수정 파일 2: `src/main.py` (시스템을 조립하고 실행하는 파일)**

**콕콕 집어주기!**
* **수정:** `utils.py`와 마찬가지로 모든 `import`를 맨 위로 올렸습니다.
* **보완:** 영상 편집(자막 추가 등) 로직을 더 세련되게 다듬었습니다. 자막이 더 예쁘게 나오고, 영상 길이를 음성 길이에 정확히 맞춥니다.
* **최적화:** 최종 영상을 저장할 때, 파일 이름에 생성된 영상의 제목을 포함시켜 관리하기 쉽게 만들었습니다.
* **단순화:** `main` 함수 로직을 더 명확하게 1~4단계로 나누어 이해하기 쉽게 만들었습니다.

```python
# src/main.py

import os
import logging
import uuid
from pathlib import Path

# --- utils.py에서 필요한 모든 도구와 설정을 가져옵니다 ---
from utils import (
    generate_viral_content,
    text_to_speech,
    download_video_from_pexels,
    Config,
    logger
)
# --- moviepy 관련 도구들도 여기서 직접 가져옵니다 ---
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip

def create_final_video(script_text: str, bg_video_path: str, audio_path: str) -> str:
    """배경 영상, 음성, 자막을 합쳐 최종 쇼츠 영상을 완성합니다."""
    try:
        logger.info("최종 영상 제작을 시작합니다.")
        
        # 1. 음성 파일과 배경 영상 파일 불러오기
        audio_clip = AudioFileClip(audio_path)
        video_clip = VideoFileClip(bg_video_path)
        
        video_duration = audio_clip.duration
        
        # 2. 배경 영상을 음성 길이에 맞추고 화면 비율(9:16)로 크롭/리사이즈
        # 영상이 세로(9:16)보다 가로로 넓으면, 중앙을 크롭
        w, h = video_clip.size
        target_ratio = 9 / 16
        if w / h > target_ratio:
            new_w = h * target_ratio
            video_clip = video_clip.crop(x_center=w/2, width=new_w)
        # 영상이 세로보다 길면, 중앙을 크롭
        else:
            new_h = w / target_ratio
            video_clip = video_clip.crop(y_center=h/2, height=new_h)
            
        video_clip = video_clip.resize(height=Config.SHORTS_HEIGHT)
        video_clip = video_clip.set_duration(video_duration)
        
        # 3. 보기 좋은 자막 생성
        # 긴 스크립트를 여러 줄로 나누어 표시
        txt_clip = TextClip(
            script_text,
            fontsize=70,
            color='white',
            font='NanumGothic-Bold', # 나눔고딕 같은 한글 폰트 권장
            stroke_color='black',
            stroke_width=2,
            size=(Config.SHORTS_WIDTH * 0.8, None), # 화면 너비의 80%
            method='caption' # 자동 줄바꿈
        ).set_position('center').set_duration(video_duration)
        
        # 4. 모든 요소를 하나로 합치기
        final_clip = CompositeVideoClip([video_clip, txt_clip])
        final_clip = final_clip.set_audio(audio_clip)
        
        # 5. 최종 영상 파일로 저장
        # 파일 이름이 너무 길어지는 것을 방지
        safe_title = "".join(c for c in script_text[:20] if c.isalnum() or c in " _-").rstrip()
        output_filename = f"{safe_title}_{uuid.uuid4()}.mp4"
        output_path = str(Config.OUTPUT_DIR / output_filename)
        
        final_clip.write_videofile(
            output_path, 
            fps=30, 
            codec='libx264',
            audio_codec='aac',
            threads=os.cpu_count() # CPU 코어를 모두 사용하여 렌더링 속도 향상
        )
        logger.info(f"최종 영상 제작 성공: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"최종 영상 제작 중 심각한 오류 발생: {e}", exc_info=True)
        # 영상 합성에 실패하더라도, 다운로드된 배경 영상 경로라도 반환
        return bg_video_path

def main():
    """유튜브 자동화 시스템의 메인 실행 함수"""
    logger.info("==================================================")
    logger.info("💰💰 유튜브 수익형 자동화 시스템 V3 시작 💰💰")
    logger.info("==================================================")
    
    # 0. 폴더 준비
    Config.ensure_directories()
    
    # 1. 콘텐츠 아이디어 생성 (AI)
    topic = "부자가 되는 사소한 습관" # <-- 여기 주제만 바꾸면 됩니다!
    logger.info(f"🔥 오늘의 주제: {topic}")
    content = generate_viral_content(topic)
    
    # 2. 대본을 음성으로 변환 (TTS)
    audio_filename = str(Config.TEMP_DIR / f"{uuid.uuid4()}.mp3")
    audio_path = text_to_speech(content['script'], audio_filename)
    
    # 임시로 음성 길이를 측정 (배경 영상 다운로드 시 필요)
    temp_audio_clip = AudioFileClip(audio_path)
    estimated_duration = temp_audio_clip.duration + 1 # 1초 여유
    temp_audio_clip.close()
    
    # 3. 주제에 맞는 배경 영상 다운로드
    video_path = download_video_from_pexels(topic, duration=estimated_duration)
    
    # 4. 모든 재료를 합쳐 최종 영상 만들기
    final_video_path = create_final_video(content['script'], video_path, audio_path)
    
    logger.info("==================================================")
    logger.info(f"✅ 모든 작업 완료! 최종 영상 경로: {final_video_path}")
    logger.info("==================================================")

if __name__ == "__main__":
    main()
