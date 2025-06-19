import os
import subprocess
from moviepy.editor import *
from src.tts_generator import generate_tts

class VideoCreator:
    def __init__(self, script: str, voice_id: str, font_path: str):
        self.script = script
        self.voice_id = voice_id
        self.font_path = font_path
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)

    def create_video(self) -> str:
        # 1. 음성 생성
        audio_path = self._generate_audio()
        
        # 2. 영상 소스 다운로드 (Pexels API 사용)
        video_clip = self._get_video_clip()
        
        # 3. 텍스트 추가
        final_clip = self._add_text_to_video(video_clip, audio_path)
        
        # 4. 출력 파일 저장
        output_path = os.path.join(self.output_dir, f"shorts_{int(time.time())}.mp4")
        final_clip.write_videofile(output_path, codec='libx264', fps=24)
        
        return output_path

    def _generate_audio(self) -> str:
        return generate_tts(self.script, self.voice_id)

    def _get_video_clip(self, duration: int = 60) -> VideoFileClip:
        # Pexels에서 무료 영상 다운로드 (실제 구현 필요)
        return VideoFileClip("assets/background.mp4").subclip(0, duration)

    def _add_text_to_video(self, video_clip: VideoFileClip, audio_path: str) -> VideoFileClip:
        audio = AudioFileClip(audio_path)
        txt_clip = TextClip(
            self.script,
            fontsize=40,
            color='white',
            font=self.font_path,
            size=video_clip.size
        ).set_duration(audio.duration)
        
        return CompositeVideoClip([video_clip, txt_clip.set_position('center')]).set_audio(audio)
