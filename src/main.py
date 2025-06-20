from src.content_generator import generate_content
from src.video_creator import create_video
from src.youtube_uploader import upload_video
from src.config import load_config
import logging

def main():
    config = load_config()
    logging.info("콘텐츠 생성 시작")
    content = generate_content(config)
    logging.info("영상 제작 시작")
    video_path = create_video(content, config)
    logging.info("유튜브 업로드 시작")
    upload_video(video_path, config)

if __name__ == "__main__":
    main()
