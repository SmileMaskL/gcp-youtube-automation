import logging
import os
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, ColorClip
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 환경변수에서 ElevenLabs API Key와 Voice ID 불러오기
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
    logging.error("❌ ELEVENLABS_API_KEY 또는 ELEVENLABS_VOICE_ID가 설정되지 않았습니다.")
    raise ValueError("ElevenLabs API Key 및 Voice ID가 필요합니다.")

# ElevenLabs 클라이언트 초기화
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

def generate_audio_from_text(text: str, voice_settings: VoiceSettings = None) -> str:
    """텍스트를 오디오로 변환하고 저장"""
    try:
        # 기본 음성 설정 (사용자 정의 설정이 없을 경우)
        if voice_settings is None:
            voice_settings = VoiceSettings(
                stability=0.5,
                similarity_boost=0.7,
                style=0.0,
                speaker_boost=True
            )
        
        audio = client.generate(
            text=text,
            voice=Voice(
                voice_id=ELEVENLABS_VOICE_ID,
                settings=voice_settings
            ),
            model="eleven_multilingual_v2"
        )
        
        output_audio_path = "output/output.mp3"
        os.makedirs("output", exist_ok=True)
        
        # 바이너리 모드로 파일 저장
        with open(output_audio_path, "wb") as f:
            f.write(audio)
            
        logging.info(f"✅ 오디오 생성 완료: {output_audio_path}")
        return output_audio_path
    except Exception as e:
        logging.error(f"🛑 ElevenLabs 오디오 생성 실패: {e}")
        raise

def create_video():
    """영상 생성 메인 함수"""
    logging.info("🎬 영상 생성 시작")
    text_to_speak = "안녕하세요. 이것은 자동화된 유튜브 비디오의 예시입니다."

    try:
        # 음성 생성 (사용자 정의 음성 설정 적용)
        custom_voice_settings = VoiceSettings(
            stability=0.7,
            similarity_boost=0.8,
            style=0.2,
            speaker_boost=True
        )
        
        audio_file = generate_audio_from_text(text_to_speak, custom_voice_settings)
        audio_clip = AudioFileClip(audio_file)
        
        # 영상 길이 = 오디오 길이 + 2초 (여유 시간)
        duration = audio_clip.duration + 2
        
        # 1080x1920 (세로형) 검은색 배경 영상 생성
        video_clip = ColorClip(
            size=(1080, 1920),
            color=(0, 0, 0),
            duration=duration
        ).set_audio(audio_clip)
        
        output_video_path = "output/final_video.mp4"
        
        # 영상 렌더링 설정
        video_clip.write_videofile(
            output_video_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=4,  # 멀티스레드 사용
            preset='fast',  # 인코딩 속도/품질 밸런스
            bitrate="5000k"  # 비트레이트 설정
        )
        
        logging.info(f"✅ 영상 생성 완료: {output_video_path}")
        return output_video_path
        
    except Exception as e:
        logging.error(f"🛑 영상 생성 실패: {e}")
        raise
    finally:
        # 리소스 정리
        if 'audio_clip' in locals():
            audio_clip.close()
        if 'video_clip' in locals():
            video_clip.close()

def example_voice_generation():
    """예제: 음성 생성 및 저장 테스트"""
    try:
        # ElevenLabs 음성 생성 예제
        test_audio = client.generate(
            text="안녕하세요. 오늘의 영상입니다.",
            voice=Voice(
                voice_id=ELEVENLABS_VOICE_ID,
                settings=VoiceSettings(
                    stability=0.6,
                    similarity_boost=0.75,
                    style=0.1,
                    speaker_boost=True
                )
            ),
            model="eleven_multilingual_v2"
        )
        
        # 테스트 오디오 저장
        test_output_path = "output/test_audio.mp3"
        os.makedirs("output", exist_ok=True)
        
        with open(test_output_path, "wb") as f:
            f.write(test_audio)
            
        logging.info(f"✅ 테스트 오디오 저장 완료: {test_output_path}")
        
    except Exception as e:
        logging.error(f"🛑 테스트 오디오 생성 실패: {e}")

if __name__ == "__main__":
    # 출력 폴더 생성
    os.makedirs("output", exist_ok=True)
    
    # 예제 음성 생성 실행
    example_voice_generation()
    
    # 메인 영상 생성 실행
    create_video()
