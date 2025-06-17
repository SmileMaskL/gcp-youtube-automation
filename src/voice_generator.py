# 목적: YouTube 자동화 시스템에서 음성 합성 기능을 수행하는 모듈
# 필요 기능: 텍스트를 음성으로 변환하여 MP3 파일로 저장
import os
from google.cloud import texttospeech
from dotenv import load_dotenv
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

def generate_voice(text: str, output_file: str = "output.mp3") -> str:
    """
    Google Cloud TTS API를 사용해 텍스트를 음성으로 변환
    
    Args:
        text: 변환할 텍스트 내용
        output_file: 출력 파일 경로 (기본값: output.mp3)
    
    Returns:
        생성된 음성 파일 경로
    """
    try:
        # GCP 클라이언트 초기화
        client = texttospeech.TextToSpeechClient()
        
        # 음성 합성 설정
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            name="ko-KR-Neural2-C",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # API 요청 실행
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # 파일 저장
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        logger.info(f"🔊 음성 파일 생성 완료: {output_file}")
        return output_file

    except Exception as e:
        logger.error(f"음성 생성 실패: {str(e)}")
        raise
