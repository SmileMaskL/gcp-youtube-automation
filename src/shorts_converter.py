import os
import logging
import sys
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.config import change_settings


logger = logging.getLogger(__name__)

# ImageMagick 경로 설정
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})


def convert_to_shorts(input_video_path: str, output_video_path: str, 
                      font_path: str = "fonts/Catfont.ttf"):
    if not os.path.exists(input_video_path):
        logger.error(f"Input video file not found: {input_video_path}")
        return False
        
    if not os.path.exists(font_path):
        logger.error(
            f"Font file not found: {font_path}. "
            "Please ensure Catfont.ttf is in the 'fonts/' directory."
        )
        font_path = "DejaVuSans-Bold"
        logger.warning(
            f"Using default font: {font_path} due to missing custom font."
        )

    try:
        logger.info(f"Loading video clip from: {input_video_path}")
        clip = VideoFileClip(input_video_path)
        
        target_width = 1080
        target_height = 1920
        aspect_ratio = clip.w / clip.h
        
        if aspect_ratio > (target_width / target_height):
            new_height = target_height
            new_width = int(new_height * aspect_ratio)
            temp_clip = clip.resize(height=new_height).crop(
                x_center=clip.w / 2, 
                y_center=clip.h / 2,
                width=target_width, 
                height=target_height
            )
            logger.info(f"Cropped wide video to {target_width}x{target_height}")
        elif aspect_ratio < (target_width / target_height):
            new_width = target_width
            new_height = int(new_width / aspect_ratio)
            temp_clip = clip.resize(width=new_width)
            
            black_background = ColorClip(
                (target_width, target_height), 
                color=(0, 0, 0)
            ).set_duration(temp_clip.duration)
            
            final_clip = CompositeVideoClip(
                [black_background, temp_clip.set_pos("center")]
            ).set_duration(temp_clip.duration)
            logger.info(
                "Added black bars to narrow video. "
                f"Resulting resolution: {target_width}x{target_height}"
            )
            clip = final_clip
        else:
            clip = clip.resize((target_width, target_height))
            logger.info(f"Resized video to {target_width}x{target_height}")
        
        if clip.duration > 60:
            clip = clip.subclip(0, 60)
            logger.info("Clipped video to 60 seconds for Shorts.")
        
        text_content = "Generated YouTube Shorts"
        text_clip = TextClip(
            text_content, 
            fontsize=70, 
            color='white', 
            font=font_path,
            stroke_color='black', 
            stroke_width=2,
            method='caption',
            size=(clip.w * 0.8, None)
        ).set_position(('center', 'top')).set_duration(clip.duration).set_opacity(0.8)
        
        final_clip = CompositeVideoClip([clip, text_clip])
        
        output_dir = os.path.dirname(output_video_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        
        logger.info(f"Writing Shorts video to: {output_video_path}")
        final_clip.write_videofile(
            output_video_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            preset="fast",
            threads=os.cpu_count() or 1,
            logger=None
        )
        logger.info(
            f"Video successfully converted to Shorts and saved to {output_video_path}"
        )
        return True
    
    except Exception as e:
        logger.error(f"Error converting video to Shorts: {e}", exc_info=True)
        return False


# 테스트 코드
if __name__ == "__main__":
    from src.config import setup_logging
    setup_logging()
    input_test_video = "dummy_video.mp4"
    output_test_shorts = "output/test_shorts_output.mp4"
    font_test_path = "fonts/Catfont.ttf"
    
    if not os.path.exists(input_test_video):
        print(
            f"Error: Test video file not found at '{input_test_video}'. "
            "Please create one or specify a valid path."
        )
        sys.exit(1)
    
    print(f"Attempting to convert '{input_test_video}' to Shorts...")
    if convert_to_shorts(input_test_video, output_test_shorts, font_path=font_test_path):
        print(f"Successfully converted to Shorts: {output_test_shorts}")
    else:
        print("Failed to convert video to Shorts.")
