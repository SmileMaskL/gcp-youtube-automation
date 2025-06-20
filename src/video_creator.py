import logging
import os
import random
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip, ColorClip, ImageClip
from elevenlabs import generate, save, Voice, VoiceSettings
from src.config import load_config
# from src.bg_downloader import download_background_video # Assuming this exists and works
# from src.thumbnail_generator import generate_thumbnail_image # Assuming this exists

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
MAX_SHORTS_DURATION = 58 # Max 60 seconds, leave some buffer
OUTPUT_DIR = "output" # Directory for generated videos and thumbnails

def download_background_video():
    """
    Placeholder for background video download logic.
    In a real scenario, this would download royalty-free stock footage.
    For demonstration, we'll assume a dummy video file exists or generate a simple one.
    You might integrate with Pexels API or similar here.
    """
    logging.info("Downloading background video (placeholder)...")
    # For a real implementation, use Pexels API key (config.get("PEXELS_API_KEY"))
    # to download royalty-free videos.
    # Example: search for 'nature', 'city', 'abstract' videos.
    # Ensure downloaded videos are licensed for commercial use and free.

    # Dummy video creation if no actual downloader is implemented yet
    dummy_video_path = os.path.join(OUTPUT_DIR, "dummy_bg.mp4")
    if not os.path.exists(dummy_video_path):
        try:
            # Create a simple black video for demonstration
            # from moviepy.editor import ColorClip
            clip = ColorClip(size=(1080, 1920), color=(0,0,0), duration=60)
            clip.write_videofile(dummy_video_path, fps=24, logger=None)
            logging.info(f"Created dummy background video: {dummy_video_path}")
        except Exception as e:
            logging.error(f"Failed to create dummy background video: {e}")
            return None
    return dummy_video_path


def generate_audio(text, config):
    """Generates audio from text using ElevenLabs."""
    elevenlabs_api_key = config.get("ELEVENLABS_API_KEY")
    voice_id = config.get("ELEVENLABS_VOICE_ID")

    if not elevenlabs_api_key or not voice_id:
        logging.error("ElevenLabs API key or voice ID not configured. Cannot generate audio.")
        return None

    try:
        logging.info(f"Generating audio with ElevenLabs for voice ID: {voice_id}")
        audio = generate(
            text=text,
            voice=Voice(
                voice_id=voice_id,
                settings=VoiceSettings(stability=0.75, similarity_boost=0.75, style=0.0, use_speaker_boost=True)
            ),
            model="eleven_multilingual_v2" # Or other suitable model
        )
        audio_path = os.path.join(OUTPUT_DIR, f"audio_{random.randint(1000,9999)}.mp3")
        save(audio, audio_path)
        logging.info(f"Audio generated and saved to {audio_path}")
        return audio_path
    except Exception as e:
        logging.error(f"Error generating audio with ElevenLabs: {e}")
        return None

def generate_thumbnail(video_path, content_title, output_dir):
    """
    Generates a thumbnail for the video.
    This is a simplified version (capturing a frame).
    For more advanced thumbnail generation, integrate with an image generation AI or template.
    """
    thumbnail_path = os.path.join(output_dir, "thumbnail.jpg")
    try:
        clip = VideoFileClip(video_path)
        # Capture a frame from the middle of the video
        clip.save_frame(thumbnail_path, t=clip.duration / 2)

        # Optionally add text to the thumbnail using PIL/Pillow or ImageClip
        # This requires `Pillow` and potentially custom font loading.
        # Example with TextClip (might not be ideal for complex thumbnail designs):
        if content_title:
            try:
                img_clip = ImageClip(thumbnail_path)
                txt_clip = TextClip(content_title, fontsize=70, color='white', font=config.get("FONT_PATH"),
                                    stroke_color='black', stroke_width=3,
                                    size=(img_clip.w * 0.8, None)).set_position(("center", "center"))
                
                final_thumb_clip = CompositeVideoClip([img_clip.set_duration(1), txt_clip.set_duration(1)])
                final_thumb_clip.save_frame(thumbnail_path, t=0) # Overwrite with text
                logging.info(f"Thumbnail generated with title: {thumbnail_path}")
            except Exception as text_e:
                logging.warning(f"Failed to add text to thumbnail: {text_e}. Using raw frame.")
        
        return thumbnail_path
    except Exception as e:
        logging.error(f"Error generating thumbnail: {e}")
        return None

def create_video(content, config):
    """
    Creates a YouTube Shorts video from generated content.
    Handles background video, audio, text overlay, and thumbnail generation.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    script = content.get("script")
    title = content.get("title")
    description = content.get("description")

    if not script:
        logging.error("No script provided for video creation.")
        return None

    # 1. Generate Audio from Script
    audio_path = generate_audio(script, config)
    if not audio_path:
        return None

    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration
    logging.info(f"Generated audio duration: {audio_duration:.2f} seconds.")

    # Ensure video is within Shorts duration (max 60s, ideally < 59s)
    target_video_duration = min(audio_duration + 2, MAX_SHORTS_DURATION) # Add a couple of seconds for buffer

    # 2. Download or use a background video
    background_video_path = download_background_video()
    if not background_video_path or not os.path.exists(background_video_path):
        logging.error("No valid background video available.")
        audio_clip.close()
        return None

    try:
        video_clip = VideoFileClip(background_video_path)
        # Ensure video is portrait (9:16) and suitable for Shorts
        if video_clip.w / video_clip.h != 9/16:
            logging.info("Resizing background video to 9:16 aspect ratio.")
            # Resize and crop to 9:16. Example: Center crop or pad.
            # For simplicity, let's just resize, which might distort if not careful.
            # A better approach is often to crop or use a fill strategy.
            # If original is landscape, crop center square then pad sides to 9:16.
            # Or if it's very wide, resize height and then crop width.
            target_width = 1080
            target_height = 1920 # Standard Shorts resolution
            
            # Simple resize for demonstration - might distort
            video_clip = video_clip.resize(newsize=(target_width, target_height))
            logging.info(f"Background video resized to {video_clip.size}")
        
        # Loop or cut background video to match audio duration
        if video_clip.duration < target_video_duration:
            video_clip = video_clip.loop(duration=target_video_duration)
            logging.info(f"Background video looped to {video_clip.duration:.2f} seconds.")
        else:
            video_clip = video_clip.subclip(0, target_video_duration)
            logging.info(f"Background video subclipped to {video_clip.duration:.2f} seconds.")

        # Set the audio of the video clip
        final_clip = video_clip.set_audio(audio_clip)

        # 3. Add Text Overlay (Subtitles based on script)
        # This part requires more advanced logic to sync text with audio.
        # For simplicity, let's just display the full script or main points as scrolling text.
        # A more robust solution involves breaking script into sentences and timing them.

        # Simple text overlay: Display the full script. This might be too fast.
        # Consider a more sophisticated way to display text chunks.
        text_clip = TextClip(script, fontsize=60, color='white', font=config.get("FONT_PATH"),
                             stroke_color='black', stroke_width=2,
                             size=(final_clip.w * 0.9, None), method='caption').set_duration(final_clip.duration).set_position(('center', 'center'))

        final_clip = CompositeVideoClip([final_clip, text_clip])

        # 4. Generate the final video file
        output_video_path = os.path.join(OUTPUT_DIR, f"youtube_shorts_{int(time.time())}.mp4")
        logging.info(f"Writing final video to {output_video_path}")
        final_clip.write_videofile(output_video_path, fps=24, codec='libx264', audio_codec='aac', bitrate="5000k", logger=None)
        
        logging.info("Video rendering complete.")

        # 5. Generate Thumbnail
        thumbnail_path = generate_thumbnail(output_video_path, title, OUTPUT_DIR)
        if thumbnail_path:
            content["thumbnail_path"] = thumbnail_path # Add thumbnail path to content for uploader
        
        # Close clips to free up resources
        audio_clip.close()
        video_clip.close()
        final_clip.close()

        # Clean up temporary audio file
        try:
            os.remove(audio_path)
            logging.info(f"Cleaned up temporary audio file: {audio_path}")
        except OSError as e:
            logging.warning(f"Error cleaning up audio file {audio_path}: {e}")

        return output_video_path
    except Exception as e:
        logging.error(f"Error during video creation: {e}")
        if 'audio_clip' in locals() and audio_clip: audio_clip.close()
        if 'video_clip' in locals() and video_clip: video_clip.close()
        if 'final_clip' in locals() and final_clip: final_clip.close()
        return None
