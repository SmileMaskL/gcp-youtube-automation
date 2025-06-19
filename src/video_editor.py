import os
import logging
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.config import change_settings

# FFMPEG 경로 설정 (GitHub Actions 환경에서는 기본 설치되어 있으나, 로컬 환경에서 필요할 수 있음)
# change_settings({"FFMPEG_BINARY": "/usr/bin/ffmpeg"}) 

logger = logging.getLogger(__name__)

def create_short_video(video_path: str, audio_path: str, text: str, font_path: str, output_path: str) -> Optional[str]:
    try:
        # 배경 영상 로드
        video_clip = VideoFileClip(video_path)
        
        # 오디오 로드
        audio_clip = AudioFileClip(audio_path)
        
        # 영상 길이 조정: 오디오 길이에 맞추거나 최대 60초
        target_duration = min(audio_clip.duration, 60)
        
        if video_clip.duration < target_duration:
            # 영상 길이가 짧으면 반복하여 채우기
            num_repeats = int(target_duration / video_clip.duration) + 1
            repeated_video_clips = [video_clip.copy().set_start(i * video_clip.duration) for i in range(num_repeats)]
            video_clip = CompositeVideoClip(repeated_video_clips).set_duration(target_duration)
        else:
            # 영상 길이가 길면 필요한 만큼만 자르기 (중앙 부분)
            start_trim = (video_clip.duration - target_duration) / 2
            video_clip = video_clip.subclip(start_trim, start_trim + target_duration)
        
        # 쇼츠 비율 (9:16)로 크기 조정
        # 원본 영상의 종횡비 확인
        original_aspect_ratio = video_clip.w / video_clip.h
        target_aspect_ratio = 9 / 16 # 쇼츠 비율

        if original_aspect_ratio > target_aspect_ratio:
            # 원본 영상이 더 가로가 길면 세로를 기준으로 자르기 (가로 크롭)
            new_width = int(video_clip.h * target_aspect_ratio)
            x_center = video_clip.w / 2
            video_clip = video_clip.crop(x1=x_center - new_width / 2, y1=0, x2=x_center + new_width / 2, y2=video_clip.h)
        else:
            # 원본 영상이 더 세로가 길거나 같으면 가로를 기준으로 자르기 (세로 크롭)
            new_height = int(video_clip.w / target_aspect_ratio)
            y_center = video_clip.h / 2
            video_clip = video_clip.crop(x1=0, y1=y_center - new_height / 2, x2=video_clip.w, y2=y_center + new_height / 2)
            
        video_clip = video_clip.resize(newsize=(720, 1280)) # 최종 쇼츠 해상도

        video_clip = video_clip.set_audio(audio_clip.set_duration(target_duration))
        video_clip = video_clip.set_duration(target_duration)
        
        # 텍스트 오버레이 (제목)
        try:
            # Catfont.ttf 사용
            font_size = 80
            text_clip = TextClip(text, fontsize=font_size, color='white', font=font_path, stroke_color='black', stroke_width=3)
        except IOError:
            logger.warning(f"폰트 파일 '{font_path}'를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
            text_clip = TextClip(text, fontsize=80, color='white', stroke_color='black', stroke_width=3)
            
        text_clip = text_clip.set_position(("center", "center")).set_duration(target_duration)

        final_clip = CompositeVideoClip([video_clip, text_clip])

        # 파일 저장 경로 확인 및 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        final_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", threads=4)
        
        return output_path
    except Exception as e:
        logger.error(f"비디오 제작 실패: {str(e)}")
        return None
