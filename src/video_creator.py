# src/video_creator.py
import os
import random
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.config import change_settings # FFmpeg 경로 설정
import logging

logger = logging.getLogger(__name__)

# FFmpeg 경로 설정 (Cloud Functions 환경에서는 PATH에 기본적으로 FFmpeg이 있을 것으로 예상되나, 
# 명시적으로 설정하여 안정성을 높일 수 있습니다. 만약 문제가 발생한다면 이 경로를 조정해야 합니다.)
# 로컬 개발 환경에서만 필요할 수 있습니다. Cloud Functions에서는 기본적으로 경로가 설정됩니다.
# try:
#     # 'ffmpeg' 명령어가 PATH에 있는지 확인하거나, 특정 경로를 지정
#     # 예를 들어, Cloud Build로 커스텀 런타임을 빌드할 경우 특정 경로에 설치 가능
#     change_settings({"FFMPEG_BINARY": "/usr/bin/ffmpeg"}) 
#     logger.info("FFMPEG_BINARY path set successfully.")
# except Exception as e:
#     logger.warning(f"Failed to set FFMPEG_BINARY path: {e}. Assuming ffmpeg is in PATH.")


class VideoCreator:
    def __init__(self, font_path, pexels_api_key): # Pexels API 키를 받도록 수정
        self.font_path = font_path
        self.pexels_api_key = pexels_api_key
        if not self.pexels_api_key:
            logger.error("Pexels API Key is not provided to VideoCreator.")
            raise ValueError("Pexels API Key is required for video creation.")

    def _download_pexels_video(self, query: str, duration_sec: int = 60):
        """Pexels에서 관련 영상을 다운로드합니다."""
        headers = {"Authorization": self.pexels_api_key}
        url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=1&size=medium"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status() # HTTP 오류 발생 시 예외
            data = response.json()
            
            if not data or not data.get('videos'):
                logger.warning(f"No Pexels videos found for query: {query}")
                return None

            video_files = data['videos'][0]['video_files']
            # 해상도 720p 이상, mp4 형식의 짧은 영상 선호
            suitable_videos = [
                v for v in video_files 
                if v['link'].endswith('.mp4') and v.get('width', 0) >= 720
            ]
            
            if not suitable_videos:
                logger.warning(f"No suitable MP4 video (>=720p) found for query: {query}")
                return None

            video_url = suitable_videos[0]['link'] # 첫 번째 적합한 영상 사용
            
            # 임시 파일로 저장
            video_filename = f"pexels_video_{uuid.uuid4().hex}.mp4"
            download_path = os.path.join("/tmp", video_filename)

            logger.info(f"Downloading Pexels video from: {video_url}")
            video_response = requests.get(video_url, stream=True, timeout=30)
            video_response.raise_for_status()

            with open(download_path, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Pexels video downloaded to {download_path}")
            return download_path

        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading Pexels video for query '{query}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Pexels video download: {e}")
            return None


    def create_video(self, audio_path, text_content, output_path):
        """주어진 오디오와 텍스트로 60초 Shorts 영상을 생성합니다."""
        try:
            audio_clip = AudioFileClip(audio_path)
            video_duration = min(audio_clip.duration + 2, 60) # 오디오 길이에 2초 추가, 최대 60초

            # Pexels에서 배경 영상 다운로드 (주제 기반)
            # 여기서는 스크립트 내용에서 키워드를 추출하여 검색 쿼리로 사용할 수 있습니다.
            # 간단하게는 "news", "abstract", "city" 등으로 고정하거나, topic에서 추출
            # 예시: 스크립트의 첫 몇 단어를 사용
            search_query = text_content.split(' ')[0] if text_content else "abstract" 
            background_video_path = self._download_pexels_video(search_query, duration_sec=int(video_duration))
            
            if background_video_path:
                background_clip = VideoFileClip(background_video_path)
                # Shorts 비율 (9:16)로 크기 조정 및 잘라내기
                target_aspect_ratio = 9/16
                current_aspect_ratio = background_clip.w / background_clip.h
                
                if current_aspect_ratio > target_aspect_ratio: # 원본이 더 넓은 경우 (좌우 자르기)
                    new_width = int(background_clip.h * target_aspect_ratio)
                    x_center = background_clip.w / 2
                    background_clip = background_clip.crop(x1=x_center - new_width/2, width=new_width)
                elif current_aspect_ratio < target_aspect_ratio: # 원본이 더 긴 경우 (상하 자르기)
                    new_height = int(background_clip.w / target_aspect_ratio)
                    y_center = background_clip.h / 2
                    background_clip = background_clip.crop(y1=y_center - new_height/2, height=new_height)
                
                # 배경 영상 길이를 오디오 길이에 맞춤
                background_clip = background_clip.subclip(0, video_duration)
                background_clip = background_clip.set_fps(24) # fps를 명시적으로 설정

            else:
                logger.warning("No background video found or downloaded. Using a black background.")
                background_clip = ColorClip(size=(1080, 1920), color=(0,0,0), duration=video_duration) # 9:16 비율
            
            # 오디오 클립을 비디오에 설정
            video_with_audio = background_clip.set_audio(audio_clip)

            # 텍스트 오버레이 (자막)
            words = text_content.split()
            clips = [video_with_audio]
            current_time = 0

            # 텍스트 클립을 위한 기본 스타일
            text_style = {
                "fontsize": 60,
                "color": 'white',
                "font": self.font_path,
                "stroke_color": 'black',
                "stroke_width": 3
            }

            # 텍스트를 여러 줄로 나누고 화면 중앙에 배치
            # 이 부분은 텍스트 길이와 화면 크기에 따라 조정 필요
            max_chars_per_line = 30 # 한 줄에 표시될 최대 글자 수 (폰트에 따라 다름)
            
            # 음성 파일에서 각 단어의 타이밍을 정확히 파악하기는 어렵습니다.
            # 간단하게는 전체 오디오 길이에 비례하여 텍스트를 분할합니다.
            # 더 정교한 자막을 위해서는 음성-텍스트 정렬(forced alignment) 라이브러리가 필요하지만,
            # Cloud Functions 환경에서 복잡하고 리소스 소모가 큽니다.
            # 여기서는 전체 텍스트를 일정 시간 간격으로 분할하여 표시합니다.
            
            sentences = text_content.split('. ') # 문장 단위로 분할
            
            current_sentence_index = 0
            sentence_display_duration = video_duration / max(1, len(sentences)) # 각 문장 표시 시간

            for i, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue

                # 문장을 여러 줄로 나누기 (너무 길면)
                wrapped_text = ""
                temp_line = ""
                for word in sentence.split(' '):
                    if len(temp_line + word) + 1 <= max_chars_per_line:
                        temp_line += (word + " ")
                    else:
                        wrapped_text += (temp_line.strip() + "\n")
                        temp_line = (word + " ")
                wrapped_text += temp_line.strip()
                
                text_clip = TextClip(
                    wrapped_text, 
                    **text_style,
                    size=(background_clip.w * 0.8, None), # 너비 제한
                    method='caption' # 텍스트 자동 줄바꿈
                )
                text_clip = text_clip.set_position("center").set_duration(sentence_display_duration)
                text_clip = text_clip.set_start(i * sentence_display_duration) # 시작 시간 설정
                clips.append(text_clip)

            final_clip = CompositeVideoClip(clips, size=(1080, 1920)) # Shorts 표준 해상도

            logger.info(f"Writing video to {output_path}...")
            final_clip.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac', 
                fps=24, # 프레임 속도 (YouTube Shorts 권장)
                threads=1, # Cloud Functions 환경에서 CPU 사용량 제한 (필요시 조정)
                logger='bar' # 진행률 바 숨김
            )
            logger.info(f"Video created successfully at {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error during video creation: {e}", exc_info=True)
            return False
