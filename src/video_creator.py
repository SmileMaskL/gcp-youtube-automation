import subprocess
import uuid
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap
from config import Config

def render_text_image(title, script, output_path):
    img = Image.new("RGB", (Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT), "black")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(Config.FONT_PATH, 60)
    
    # 제목 렌더링
    draw.text((50, 200), title, font=font, fill="white")
    
    # 대본 렌더링
    y_offset = 400
    for line in textwrap.wrap(script, width=40):
        draw.text((50, y_offset), line, font=font, fill="white")
        y_offset += 70
    
    img.save(output_path)

def create_video(content, audio_path, bg_path):
    output_path = Config.OUTPUT_DIR / f"shorts_{uuid.uuid4()}.mp4"
    text_image = Config.TEMP_DIR / f"text_{uuid.uuid4()}.png"
    
    render_text_image(content["title"], content["script"], text_image)
    
    subprocess.run([
        "ffmpeg",
        "-i", str(bg_path),
        "-i", str(text_image),
        "-i", str(audio_path),
        "-filter_complex",
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[bg];"
        "[bg][1:v]overlay=0:0[vid]",
        "-map", "[vid]",
        "-map", "2:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        "-y", str(output_path)
    ], check=True)
    
    return output_path
