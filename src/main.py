import os
import uuid
import requests
from pathlib import Path
from core.config import Config

def generate_tts_with_elevenlabs(script: str) -> str:
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    api_key = os.getenv("ELEVENLABS_API_KEY")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    json_data = {
        "text": script,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    response = requests.post(url, headers=headers, json=json_data)
    if response.status_code != 200:
        raise Exception(f"TTS 실패: {response.status_code} - {response.text}")

    audio_path = Config.TEMP_DIR / f"audio_{uuid.uuid4()}.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.content)

    return str(audio_path)

    except Exception as e:
        logger.error(f"[TTS 실패] {e}")
        raise

def download_video_from_pexels(query: str, duration: int) -> str:
    try:
        headers = {"Authorization": os.getenv("PEXELS_API_KEY")}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=3"
        response = requests.get(url, headers=headers, timeout=15)
        videos = response.json().get('videos', [])
        if not videos:
            return create_simple_video(duration)
        video_url = videos[0]['video_files'][0]['link']
        path = Config.TEMP_DIR / f"pexels_{uuid.uuid4()}.mp4"
        with requests.get(video_url, stream=True) as r:
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return str(path)
    except:
        return create_simple_video(duration)


def create_simple_video(duration=60) -> str:
    color = random.choice([(0, 0, 0), (30, 30, 30), (50, 50, 50)])
    path = Config.TEMP_DIR / f"bg_{uuid.uuid4()}.mp4"
    clip = ColorClip(size=(Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT), color=color, duration=duration)
    clip.write_videofile(str(path), fps=24, logger=None)
    return str(path)


def create_shorts_video(video_path: str, audio_path: str, title: str) -> str:
    try:
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)

        if video.duration < audio.duration:
            video = video.loop(duration=audio.duration)
        else:
            video = video.subclip(0, audio.duration)

        txt = TextClip(
            title,
            fontsize=60,
            color="white",
            font="Arial-Bold",
            size=(1080, None),
            method="caption"
        ).set_duration(audio.duration).set_position("center")

        final = CompositeVideoClip([video, txt]).set_audio(audio)
        output = Config.OUTPUT_DIR / f"shorts_{uuid.uuid4()}.mp4"
        final.write_videofile(str(output), fps=24)
        return str(output)
    except Exception as e:
        logger.error(f"[영상 생성 실패] {e}")
        raise


def cleanup_temp_files():
    for f in Config.TEMP_DIR.glob("*"):
        try:
            f.unlink()
        except:
            pass


def main():
    topic = "부자 되는 법"
    logger.info("🚀 유튜브 쇼츠 자동 생성 시작")
    content = generate_viral_content_gemini(topic)
    logger.info(f"🎯 콘텐츠: {content}")
    audio_path = generate_tts_with_elevenlabs(content["script"])
    bg_video = download_video_from_pexels(topic, 60)
    final = create_shorts_video(bg_video, audio_path, content["title"])
    logger.info(f"🎉 영상 저장 완료: {final}")
    cleanup_temp_files()


if __name__ == "__main__":
    main()
