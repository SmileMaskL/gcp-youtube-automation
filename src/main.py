import os
from dotenv import load_dotenv
from .content_generator import ContentGenerator
from .tts_generator import TTSGenerator
from .video_creator import VideoCreator
from .youtube_uploader import YouTubeUploader
from .usage_tracker import UsageTracker
from .error_handler import log_error

def main():
    # 환경 변수 로드
    load_dotenv()
    
    try:
        # 1. 콘텐츠 생성
        generator = ContentGenerator()
        content = generator.generate_script()
        
        # 2. 음성 생성
        tts = TTSGenerator()
        audio_path = tts.generate_audio(content['script'])
        
        # 3. 영상 생성
        creator = VideoCreator()
        video_path = creator.create_video(
            audio_path=audio_path,
            script=content['script'],
            title=content['topic']
        )
        
        # 4. YouTube 업로드
        uploader = YouTubeUploader()
        uploader.upload_video(
            file_path=video_path,
            title=content['topic'],
            description=content['script'][:5000]  # 설명은 5000자로 제한
        )
        
        # 5. 사용량 추적
        tracker = UsageTracker()
        tracker.record_usage(
            service='openai',
            tokens_used=len(content['script']) // 4  # 대략적인 토큰 계산
        )
        
    except Exception as e:
        log_error(str(e))
        raise

if __name__ == "__main__":
    main()
