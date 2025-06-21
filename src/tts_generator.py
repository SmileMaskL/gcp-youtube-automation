# src/tts_generator.py
import os
import logging
from elevenlabs import generate, Voice, VoiceSettings, set_api_key

logger = logging.getLogger(__name__)

def generate_audio(text: str, output_path: str, api_key: str, voice_id: str = "uyVNoMrnUku1dZyVEXwD"):
    """
    ElevenLabs API를 사용하여 텍스트로부터 오디오를 생성하고 저장합니다.

    Args:
        text (str): 오디오로 변환할 텍스트.
        output_path (str): 생성된 오디오 파일을 저장할 경로.
        api_key (str): ElevenLabs API 키.
        voice_id (str): 사용할 ElevenLabs 음성 ID (기본값은 '안나 킴').

    Returns:
        bool: 오디오 생성 및 저장이 성공하면 True, 실패하면 False.
    """
    if not api_key:
        logger.error("ElevenLabs API Key is not provided. Cannot generate audio.")
        raise ValueError("ElevenLabs API Key is missing.")
    
    # ElevenLabs API 키 설정
    set_api_key(api_key)
    
    try:
        logger.info(f"Generating audio for text (first 50 chars): '{text[:50]}...' with voice_id: {voice_id}")
        audio_stream = generate(  # audio_stream은 제너레이터 객체입니다.
            text=text,
            voice=Voice(
                voice_id=voice_id,
                settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
            ),
            model="eleven_multilingual_v2" # 다국어 모델 명시
        )
        
        # 출력 디렉토리 생성
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        
        # 제너레이터에서 데이터를 읽어와 파일에 쓰기
        with open(output_path, "wb") as f:
            for chunk in audio_stream: # 제너레이터에서 청크(데이터 조각)를 반복적으로 읽어옵니다.
                if chunk:
                    f.write(chunk) # 각 청크를 파일에 씁니다.
        
        logger.info(f"Audio successfully saved to {output_path}")
        return True

    except Exception as e:
        logger.error(f"ElevenLabs API error during audio generation: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # 이 부분은 로컬 테스트용이며, 실제 배포에서는 환경 변수를 통해 API 키를 주입합니다.
    # 테스트를 위해 실제 키를 여기에 직접 넣지 마세요!
    sample_api_key = os.environ.get("ELEVENLABS_API_KEY", "YOUR_ELEVENLABS_API_KEY_HERE_FOR_LOCAL_TESTING")
    sample_text = "안녕하세요. 이것은 ElevenLabs 음성 생성 테스트입니다. 잘 들리시나요?"
    sample_output_path = "output/test_audio.mp3"

    if sample_api_key == "YOUR_ELEVENLABS_API_KEY_HERE_FOR_LOCAL_TESTING":
        logger.warning("Please set ELEVENLABS_API_KEY environment variable for local testing.")
    else:
        logging.basicConfig(level=logging.INFO)
        if generate_audio(sample_text, sample_output_path, sample_api_key):
            print(f"Test audio generated at {sample_output_path}")
        else:
            print("Failed to generate test audio.")
