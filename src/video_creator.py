# src/video_creator.py

from moviepy.editor import TextClip, CompositeVideoClip, ColorClip
import os

class VideoCreator:
    def __init__(self, width=720, height=1280, bg_color=(255,255,255), fps=24):
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.fps = fps
    
    def create_video(self, script_text, output_path):
        if not script_text or len(script_text.strip()) < 10:
            raise ValueError("스크립트가 너무 짧거나 없습니다.")
        
        # 배경색 클립 (흰색 배경)
        bg_clip = ColorClip(size=(self.width, self.height), color=self.bg_color, duration=10)
        
        # 텍스트 클립 (스크립트 텍스트)
        txt_clip = TextClip(script_text, fontsize=40, color='black', size=(self.width-100, None), method='caption')
        txt_clip = txt_clip.set_position('center').set_duration(10)
        
        # 영상 합성
        video = CompositeVideoClip([bg_clip, txt_clip])
        video = video.set_fps(self.fps)
        
        # 파일 저장 (mp4)
        video.write_videofile(output_path, codec='libx264', audio=False, verbose=False, logger=None)
        
        print(f"✅ 영상 생성 완료: {output_path}")
        return output_path


if __name__ == "__main__":
    # 테스트용
    vc = VideoCreator()
    vc.create_video("안녕하세요! 이것은 테스트 영상입니다.", "output/test_video.mp4")
