from src.config import Config
from src.content_generator import generate_content
from src.video_editor import create_video
from src.youtube_uploader import upload_video
import logging

def main():
    try:
        # 1. 콘텐츠 생성
        content = generate_content()
        
        # 2. 영상 제작
        video_path = create_video(content)
        
        # 3. 유튜브 업로드
        upload_video(video_path)
        
    except Exception as e:
        logging.error(f"배치 처리 실패: {str(e)}")

if __name__ == "__main__":
    main()
