"""
TTS 생성 모듈 (최종 수정본)
"""
import requests
import logging
from pathlib import Path
from .config import Config

logger = logging.getLogger(__name__)

def text_to_speech(text: str, output_path: str):
    """
    ElevenLabs API를 사용하여 텍스트를 음성으로 변환
    """
    try:
        # 입력 텍스트 검증
        if not text or not text.strip():
            raise ValueError("TTS 생성할 텍스트가 비어있습니다")
        
        # API 엔드포인트 설정
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{Config.ELEVENLABS_VOICE_ID}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": Config.get_api_key("ELEVENLABS_API_KEY")
        }

        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        logger.info("ElevenLabs API에 TTS 요청 전송")
        
        # API 요청
        response = requests.post(
            url,
            json=data,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()

        # 오디오 파일 저장
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"TTS 오디오 파일 저장 완료: {output_path}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"TTS API 요청 실패: {e}")
        raise
    except Exception as e:
        logger.error(f"TTS 생성 중 오류 발생: {e}")
        raise
