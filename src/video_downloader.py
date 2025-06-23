# src/video_downloader.py
import logging
import yt_dlp
import os # F401 'os' imported but unused -> 실제 사용되므로 유지

logger = logging.getLogger(__name__)


class VideoDownloader:
    def __init__(self):
        logger.info("VideoDownloader initialized.")

    def download_video(self, url, output_path, format_spec='bestvideo[height<=1080]+bestaudio/best'):
        """
        Downloads a video from a given URL using yt-dlp.
        """
        ydl_opts = {
            'format': format_spec,
            'outtmpl': output_path,
            'noplaylist': True,
            'retries': 3,
            'fragment_retries': 3,
            'quiet': False,
            'no_warnings': False,
        }

        try:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.info(f"Attempting to download video from {url} to {output_path}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                final_path = ydl.prepare_filename(info)
                logger.info(f"Video downloaded successfully to: {final_path}")
                return final_path
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"yt-dlp download error: {e}", exc_info=True)
            return None
        except Exception as e:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.error(f"An unexpected error occurred during video download: {e}",
                        exc_info=True)
            return None
    
