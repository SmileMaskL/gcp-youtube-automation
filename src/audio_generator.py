# src/audio_generator.py
import requests
import logging
import os
from elevenlabs import set_api_key as set_elevenlabs_key, generate as generate_elevenlabs_audio # 실제 사용

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # 모듈별 로거 사용 권장
logger.setLevel(logging.INFO)

def generate_audio_from_text(text, elevenlabs_api_key, voice_id, output_path):
    """
    Eleven Labs API를 사용하여 텍스트로부터 음성을 생성합니다.
    :param text: 음성으로 변환할 텍스트
    :param elevenlabs_api_key: Eleven Labs API 키
    :param voice_id: 사용할 Eleven Labs 음성 ID (예: "21m00Tcm4azwk8nxvUGp")
    :param output_path: 생성된 오디오를 저장할 파일 경로 (예: "output_audio.mp3")
    """
    logger.info(f"Eleven Labs로 음성 생성 시작. 음성 ID: {voice_id}")
    
    try:
        set_elevenlabs_key(elevenlabs_api_key)
        audio = generate_elevenlabs_audio(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2" # 다국어 지원 모델
        )
        with open(output_path, "wb") as f:
            f.write(audio)
        logger.info(f"음성 파일 저장 완료: {output_path}")
    except Exception as e:
        logger.error(f"Eleven Labs API 요청 실패 또는 음성 파일 저장 중 오류 발생: {e}")
        raise

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID") # 예: "21m00Tcm4azwk8nxvUGp" (Rachel)

    if not elevenlabs_api_key or not elevenlabs_voice_id:
        print("ELEVENLABS_API_KEY와 ELEVENLABS_VOICE_ID를 .env 파일에 설정해주세요.")
    else:
        sample_text = "안녕하세요. 이것은 텍스트 음성 변환 테스트입니다. YouTube 쇼츠 자동화를 위한 첫 걸음입니다."
        output_file = "test_audio.mp3"
        try:
            generate_audio_from_text(sample_text, elevenlabs_api_key, elevenlabs_voice_id, output_file)
            print(f"'{output_file}' 파일이 성공적으로 생성되었습니다.")
        except Exception as e:
            print(f"오디오 생성 중 오류 발생: {e}")
