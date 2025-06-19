import logging
from datetime import datetime
from src.ai_rotation import AIRotator
from src.content_generator import ContentGenerator
from src.video_creator import VideoCreator
from src.youtube_uploader import YouTubeUploader
from src.usage_tracker import UsageTracker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/youtube_automation.log'
)

def main():
    try:
        # 1. API 키 로테이션 설정
        ai_rotator = AIRotator()
        api_key, ai_type = ai_rotator.get_ai_key()
        
        # 2. 콘텐츠 생성
        content_gen = ContentGenerator(api_key, ai_type)
        topic = content_gen.get_daily_topic()
        script = content_gen.generate_script(topic)
        
        # 3. 영상 제작
        video_creator = VideoCreator(
            script=script,
            voice_id=os.getenv('ELEVENLABS_VOICE_ID'),
            font_path='fonts/Catfont.ttf'
        )
        video_path = video_creator.create_video()
        
        # 4. 유튜브 업로드
        uploader = YouTubeUploader(Config.get_youtube_creds())
        uploader.upload_video(
            video_path,
            title=f"{topic} 🚀 최신 트렌드",
            description=f"{topic}에 관한 최신 정보입니다. #shorts #트렌드"
        )
        
        # 5. 사용량 추적
        tracker = UsageTracker(os.getenv('GCP_BUCKET_NAME'))
        tracker.record_usage('youtube_uploads')
        
    except Exception as e:
        logging.error(f"배치 처리 실패: {str(e)}")
        raise

if __name__ == "__main__":
    main()
