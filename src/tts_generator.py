# src/tts_generator.py

import requests
import logging
from src.config import config
from .config import config


logger = logging.getLogger(__name__)

def text_to_speech(text: str, output_path: str):
    """
    ElevenLabs API를 사용하여 텍스트를 음성으로 변환하고 파일로 저장합니다.
    """
    # ★★★ 방어 코드 추가 ★★★
    # 만약 스크립트가 비어있거나 공백뿐이라면, TTS 요청을 보내지 않고 함수를 종료합니다.
    if not text or not text.strip():
        logger.warning("TTS 생성을 위한 텍스트가 비어있어 작업을 건너뜁니다.")
        raise ValueError("TTS를 위한 스크립트가 비어있습니다.")

    # ElevenLabs API 엔드포인트 및 설정
    # 목소리 ID는 ElevenLabs 홈페이지에서 원하는 목소리를 골라 ID를 복사해오세요.
    # 예시: 'Rachel' 목소리 ID
    voice_id = "21m00Tcm4TlvDq8ikWAM" 
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": config.ELEVENLABS_API_KEY
    }

    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2", # 다국어 지원 모델
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    logger.info("ElevenLabs API에 TTS 요청을 보냅니다.")
    try:
        response = requests.post(url, json=data, headers=headers, timeout=180) # 타임아웃 180초
        response.raise_for_status()  # HTTP 오류가 발생하면 예외를 발생시킴

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"음성 파일이 성공적으로 저장되었습니다: {output_path}")

    except requests.exceptions.RequestException as e:
        logger.error(f"ElevenLabs API 요청 실패: {e}", exc_info=True)
        raise
