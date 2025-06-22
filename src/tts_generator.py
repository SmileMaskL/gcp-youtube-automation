    # src/tts_generator.py

    import logging
    from elevenlabs import Voice, VoiceSettings, generate, save

    logger = logging.getLogger(__name__)

    def generate_tts_audio(elevenlabs_api_key, text_content, voice_id, output_path):
        """
        ElevenLabs API를 사용하여 텍스트를 음성 오디오 파일로 변환합니다.
        
        Args:
            elevenlabs_api_key (str): ElevenLabs API 키.
            text_content (str): 음성으로 변환할 텍스트 내용.
            voice_id (str): 사용할 ElevenLabs 음성 ID.
            output_path (str): 생성된 오디오 파일을 저장할 경로 (예: /tmp/audio.mp3).
        """
        try:
            logger.info(f"ElevenLabs 음성 생성 시작. 음성 ID: {voice_id}, 텍스트 길이: {len(text_content)}")

            # ElevenLabs API 호출
            audio = generate(
                text=text_content,
                voice=Voice(
                    voice_id=voice_id,
                    settings=VoiceSettings(
                        stability=0.7, # 안정성 (0.0 ~ 1.0)
                        similarity_boost=0.8, # 유사성 부스트 (0.0 ~ 1.0)
                        style=0.0, # 스타일 (0.0 ~ 1.0)
                        use_speaker_boost=True # 스피커 부스트 사용 여부
                    )
                ),
                api_key=elevenlabs_api_key
            )
            
            # 오디오 파일 저장
            save(audio, output_path)
            logger.info(f"음성 파일 생성 성공: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"ElevenLabs 음성 생성 실패: {e}", exc_info=True)
            raise # 오류를 다시 발생시켜 main.py에서 처리하도록 합니다.
    
