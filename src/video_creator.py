# src/video_creator.py

import logging
import os
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, ColorClip # 필요한 모듈 임포트
from elevenlabs.client import ElevenLabsClient # ElevenLabsClient를 임포트
from elevenlabs.types import Voice, VoiceSettings # Voice, VoiceSettings의 올바른 임포트 경로

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ElevenLabs API 키는 환경 변수에서 가져오는 것이 가장 안전합니다.
# GitHub Actions Secrets에 ELEVENLABS_API_KEY로 저장했다고 가정합니다.
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    logging.error("ELEVENLABS_API_KEY environment variable is not set.")
    raise ValueError("ElevenLabs API Key is required.")

# ElevenLabs 클라이언트 초기화
elevenlabs_client = ElevenLabsClient(api_key=ELEVENLABS_API_KEY)

# --- ElevenLabs API 사용 방식 수정 ---
def generate_audio_from_text(text: str, voice_id: str = "21m00Tcm4NF8gDrvWzCj") -> str:
    """
    텍스트를 ElevenLabs API를 사용하여 오디오로 변환하고 로컬 파일로 저장합니다.
    기본 음성 ID는 'Rachel'입니다.
    """
    try:
        # elevenlabs_client.generate() 메서드 사용
        audio = elevenlabs_client.generate(
            text=text,
            voice=voice_id, # voice_id 문자열로 전달
            model="eleven_multilingual_v2" # 필요에 따라 모델 지정
        )

        output_audio_path = "generated_audio.mp3"
        # save 함수는 elevenlabs 라이브러리의 최상위 모듈에 여전히 존재할 가능성이 높습니다.
        from elevenlabs import save
        save(audio, output_audio_path)
        logging.info(f"Audio generated and saved to {output_audio_path}")
        return output_audio_path
    except Exception as e:
        logging.error(f"Failed to generate audio with ElevenLabs: {e}")
        raise

# --- 비디오 생성 함수 (예시) ---
def create_video():
    """
    더미 비디오 생성 로직 (실제 구현에 따라 수정 필요)
    """
    logging.info("Starting video creation process...")

    # 예시 텍스트로 오디오 생성
    text_to_speak = "안녕하세요. 이것은 자동화된 유튜브 비디오의 예시입니다. 모든 것이 완벽하게 작동하고 있습니다."
    try:
        audio_file = generate_audio_from_text(text_to_speak)
    except Exception as e:
        logging.error(f"Failed to generate audio for video creation: {e}")
        return # 오디오 생성 실패 시 종료

    # 더미 비디오 클립 생성 (실제 비디오 소스를 사용해야 함)
    # 여기서는 간단히 검은색 배경 비디오를 만듭니다.
    video_duration = AudioFileClip(audio_file).duration + 2 # 오디오 길이에 2초 추가
    final_clip = ColorClip(size=(1280, 720), color=(0,0,0), duration=video_duration)

    # 오디오를 비디오에 추가
    audio_clip = AudioFileClip(audio_file)
    final_clip = final_clip.set_audio(audio_clip)

    output_video_path = "final_youtube_video.mp4"
    final_clip.write_videofile(output_video_path, fps=24, codec="libx264") # 코덱 지정 (ffmpeg 설치 필수)

    logging.info(f"Video created successfully at {output_video_path}")
    logging.info("Video creation process completed.")

# 필요한 경우 Shorts 변환, 썸네일 생성 등의 함수도 여기에 구현합니다.
# def convert_to_shorts(video_path):
#    # ... Shorts 변환 로직 ...
#    pass

# def generate_thumbnail(video_path):
#    # ... 썸네일 생성 로직 ...
#    pass
