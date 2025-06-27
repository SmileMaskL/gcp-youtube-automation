# src/video_creator.py
import os
import logging
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip, ColorClip, ImageClip
from moviepy.video.tools.subtitles import SubtitlesClip
import textwrap # 자막 줄바꿈을 위해
from PIL import Image # 이미지 처리 및 리사이징

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_pexels_media(query: str, pexels_api_key: str, media_type: str = "videos", max_results: int = 5) -> list[str]:
    """
    Pexels API를 사용하여 검색 쿼리에 해당하는 비디오 또는 이미지를 다운로드합니다.
    다운로드된 파일 경로 리스트를 반환합니다.
    """
    if not pexels_api_key:
        logging.error("Pexels API key is missing.")
        return []

    headers = {"Authorization": pexels_api_key}
    downloaded_files = []
    temp_dir = "temp_pexels_media"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        if media_type == "videos":
            url = f"https://api.pexels.com/videos/search?query={query}&per_page={max_results}&orientation=portrait" # 쇼츠에 맞는 세로 영상 우선
        elif media_type == "photos":
            url = f"https://api.pexels.com/v1/search?query={query}&per_page={max_results}&orientation=portrait" # 쇼츠에 맞는 세로 이미지 우선
        else:
            logging.error(f"Unsupported media type: {media_type}")
            return []

        response = requests.get(url, headers=headers)
        response.raise_for_status() # HTTP 에러 시 예외 발생
        data = response.json()

        if media_type == "videos":
            videos = data.get("videos", [])
            for i, video_data in enumerate(videos):
                # 가장 큰 해상도 (또는 적절한 해상도) 비디오 파일 찾기
                video_files = video_data.get("video_files", [])
                hd_video = next((f for f in video_files if f['quality'] == 'hd' and f['file_type'] == 'video/mp4'), None)
                if not hd_video:
                    hd_video = next((f for f in video_files if f['file_type'] == 'video/mp4'), video_files[0] if video_files else None)

                if hd_video:
                    video_url = hd_video['link']
                    file_name = os.path.join(temp_dir, f"pexels_video_{query}_{i}.mp4")
                    logging.info(f"Downloading video from Pexels: {video_url}")
                    video_response = requests.get(video_url, stream=True)
                    video_response.raise_for_status()
                    with open(file_name, "wb") as f:
                        for chunk in video_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    downloaded_files.append(file_name)
                    logging.info(f"Downloaded: {file_name}")
        elif media_type == "photos":
            photos = data.get("photos", [])
            for i, photo_data in enumerate(photos):
                photo_url = photo_data['src'].get('original', photo_data['src']['large2x']) # 최고 품질 또는 큰 이미지
                file_name = os.path.join(temp_dir, f"pexels_photo_{query}_{i}.jpeg")
                logging.info(f"Downloading photo from Pexels: {photo_url}")
                photo_response = requests.get(photo_url, stream=True)
                photo_response.raise_for_status()
                with open(file_name, "wb") as f:
                    for chunk in photo_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                downloaded_files.append(file_name)
                logging.info(f"Downloaded: {file_name}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading Pexels media: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"An unexpected error occurred during Pexels media download: {e}", exc_info=True)
    
    return downloaded_files


def create_youtube_video(pexels_api_key: str, audio_file_path: str, keywords: list[str]) -> str | None:
    """
    Pexels에서 비디오 클립을 가져오고 오디오 파일을 결합하여 YouTube Shorts 비디오를 생성합니다.
    """
    if not os.path.exists(audio_file_path):
        logging.error(f"Audio file not found at {audio_file_path}")
        return None

    logging.info("Starting video creation process...")

    # 쇼츠 표준 해상도 (9:16 비율)
    W, H = 1080, 1920
    FPS = 30 # 프레임레이트

    # 오디오 클립 로드
    audio_clip = AudioFileClip(audio_file_path)
    audio_duration = audio_clip.duration
    logging.info(f"Audio duration: {audio_duration:.2f} seconds.")

    # Pexels에서 키워드 기반으로 비디오 또는 이미지 다운로드
    # 주요 키워드 중 하나를 선택하여 검색하거나, 여러 키워드로 검색 후 조합
    search_query = random.choice(keywords) if keywords else "technology"
    video_paths = download_pexels_media(search_query, pexels_api_key, media_type="videos", max_results=5)
    
    # 만약 비디오가 없으면 이미지로 대체
    if not video_paths:
        logging.warning("No relevant videos found from Pexels. Trying to download photos.")
        photo_paths = download_pexels_media(search_query, pexels_api_key, media_type="photos", max_results=5)
        if photo_paths:
            # 이미지들을 비디오 클립으로 변환 (각 이미지 3초씩)
            video_clips = []
            for img_path in photo_paths:
                try:
                    img_clip = ImageClip(img_path).set_duration(3).set_fps(FPS)
                    # 이미지를 쇼츠 비율에 맞게 크롭하거나 리사이즈
                    if img_clip.w / img_clip.h > W / H: # 이미지가 와이드하면 높이에 맞춰 자르기
                        img_clip = img_clip.resize(height=H).crop(x_center=img_clip.w/2, width=W)
                    else: # 이미지가 좁으면 너비에 맞춰 자르기
                        img_clip = img_clip.resize(width=W).crop(y_center=img_clip.h/2, height=H)
                    video_clips.append(img_clip)
                    logging.info(f"Processed image: {img_path}")
                except Exception as e:
                    logging.error(f"Error processing image {img_path}: {e}")
            if video_clips:
                main_video_clip = concatenate_videoclips(video_clips)
                logging.info("Converted images to video clips.")
            else:
                logging.error("Failed to create video from photos. Using a black background.")
                main_video_clip = ColorClip((W, H), color=(0,0,0), duration=audio_duration)
        else:
            logging.error("No media found from Pexels. Creating a black background video.")
            main_video_clip = ColorClip((W, H), color=(0,0,0), duration=audio_duration)
    else:
        # 다운로드된 비디오 클립들을 연결
        video_clips = []
        for vid_path in video_paths:
            try:
                clip = VideoFileClip(vid_path)
                # 클립을 쇼츠 비율에 맞게 리사이즈하거나 크롭
                if clip.w / clip.h > W / H: # 원본이 와이드하면 높이에 맞춰 자르기
                    clip = clip.resize(height=H).crop(x_center=clip.w/2, width=W)
                else: # 원본이 좁으면 너비에 맞춰 자르기
                    clip = clip.resize(width=W).crop(y_center=clip.h/2, height=H)
                video_clips.append(clip)
                logging.info(f"Processed video clip: {vid_path}")
            except Exception as e:
                logging.error(f"Error processing video clip {vid_path}: {e}")
        
        if video_clips:
            # 모든 클립을 이어 붙이고 오디오 길이에 맞춰 자르기
            main_video_clip = concatenate_videoclips(video_clips).set_fps(FPS).subclip(0, audio_duration)
            # 만약 연결된 비디오 길이가 오디오보다 짧다면 반복해서 붙임
            if main_video_clip.duration < audio_duration:
                logging.info("Concatenated video is shorter than audio. Looping video clips.")
                main_video_clip = main_video_clip.loop(duration=audio_duration)
            logging.info("Concatenated video clips.")
        else:
            logging.error("Failed to concatenate video clips. Using a black background.")
            main_video_clip = ColorClip((W, H), color=(0,0,0), duration=audio_duration)
    
    # 메인 비디오 클립의 길이를 오디오 길이에 맞춤
    main_video_clip = main_video_clip.set_duration(audio_duration)

    # 텍스트 자막 (선택 사항: TTS 스크립트에서 자막 생성 로직 추가 가능)
    # 예시 자막 (실제 스크립트를 기반으로 생성해야 함)
    # def create_subtitle_clip(text, duration):
    #     wrapped_text = textwrap.fill(text, width=30) # 글자 수에 따라 줄바꿈
    #     return TextClip(wrapped_text, fontsize=70, color='white', bg_color='black',
    #                     font='NanumGothicBold', stroke_color='black', stroke_width=2,
    #                     align='center', method='caption', size=(W*0.9, None)).set_duration(duration)

    # subtitles = [
    #     ("Hello everyone!", 0, 3),
    #     ("This is an automated YouTube Shorts video!", 3, 6),
    #     ("Powered by AI!", 6, 9)
    # ]
    # subtitle_clips = [create_subtitle_clip(txt, end-start).set_start(start).set_end(end)
    #                   for txt, start, end in subtitles]

    # 오디오를 메인 비디오 클립에 추가
    final_clip = main_video_clip.set_audio(audio_clip)
    # 자막 클립이 있다면 함께 Composite (예: final_clip = CompositeVideoClip([final_clip] + subtitle_clips))

    output_video_path = os.path.join(os.getcwd(), "final_shorts_video.mp4")
    logging.info(f"Writing final video to {output_video_path}")
    
    # 비디오 파일 출력
    final_clip.write_videofile(
        output_video_path, 
        codec="libx264", 
        audio_codec="aac", 
        fps=FPS, 
        preset="medium", # "fast", "medium", "slow" 등 선택
        threads=8 # CPU 코어 수에 맞게 조절하여 인코딩 속도 향상
    )
    
    # 임시 Pexels 미디어 파일 정리
    for f in downloaded_files:
        if os.path.exists(f):
            os.remove(f)
            logging.info(f"Cleaned up temporary Pexels file: {f}")
    if os.path.exists(temp_dir):
        os.rmdir(temp_dir)
        logging.info(f"Cleaned up temporary Pexels directory: {temp_dir}")

    logging.info("Video creation complete.")
    return output_video_path

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # 로컬 테스트용
    test_pexels_key = os.environ.get("PEXELS_API_KEY")

    # 더미 오디오 파일 생성 (실제 테스트 시에는 유효한 오디오 파일 경로로 변경)
    dummy_audio_file = "dummy_audio.mp3"
    with open(dummy_audio_file, "w") as f:
        f.write("This is a dummy audio file content for testing.")

    if not test_pexels_key:
        logging.error("PEXELS_API_KEY environment variable not set for local testing.")
        logging.info("Please set this variable to run local video creation test.")
    else:
        test_keywords = ["technology", "innovation", "future"]
        final_video = create_youtube_video(test_pexels_key, dummy_audio_file, test_keywords)
        if final_video:
            print(f"Test video created: {final_video}")
        else:
            print("Failed to create test video.")
    
    if os.path.exists(dummy_audio_file):
        os.remove(dummy_audio_file)
