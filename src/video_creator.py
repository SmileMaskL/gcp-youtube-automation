import os
from moviepy.editor import *
from gtts import gTTS
import requests
from pexels_api import API

def create_video(script: str, topic: str) -> str:
    """스크립트를 바탕으로 영상 생성"""
    try:
        # 1. 텍스트를 음성으로 변환 (무료 gTTS 사용)
        tts = gTTS(script, lang='ko')
        audio_file = f"{topic}_audio.mp3"
        tts.save(audio_file)
        
        # 2. Pexels에서 무료 영상 다운로드
        pexels = API(os.getenv("PEXELS_API_KEY"))
        search = pexels.search_video(topic, page=1, results_per_page=1)
        if search['videos']:
            video_url = search['videos'][0]['video_files'][0]['link']
            video_content = requests.get(video_url).content
            with open(f"{topic}_bg.mp4", 'wb') as f:
                f.write(video_content)
        
        # 3. 영상 편집
        clip = VideoFileClip(f"{topic}_bg.mp4").subclip(0, 60)  # 60초 영상
        audio = AudioFileClip(audio_file)
        final = clip.set_audio(audio)
        output_file = f"{topic}_final.mp4"
        final.write_videofile(output_file, fps=24)
        
        return output_file
    except Exception as e:
        print(f"❌ 영상 생성 오류: {e}")
        raise
