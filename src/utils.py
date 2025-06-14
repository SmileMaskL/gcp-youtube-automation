import os
import json
import uuid
import random
import logging
import requests
from pathlib import Path
from moviepy.editor import VideoFileClip, ColorClip, concatenate_videoclips, CompositeVideoClip
from moviepy.video.fx import resize
import google.generativeai as genai
from elevenlabs import ElevenLabs
from config import Config

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_json_response(text: str) -> str:
    """AI 응답에서 JSON 부분만 추출합니다."""
    text = text.strip()
    
    # JSON 블록 찾기
    json_start = text.find('```json')
    if json_start != -1:
        json_start += 7
        json_end = text.find('```', json_start)
        if json_end != -1:
            return text[json_start:json_end].strip()
    
    # 중괄호로 시작하는 JSON 찾기
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text[start_idx:end_idx + 1]
    
    logger.warning("응답에서 JSON 형식을 찾지 못했습니다. 원본 텍스트를 반환합니다.")
    return text

def generate_viral_content_gpt4o(topic: str) -> dict:
    """GPT-4o를 사용하여 바이럴 콘텐츠를 생성합니다."""
    try:
        logger.info("GPT-4o를 사용하여 콘텐츠를 생성합니다.")
        # 실제로는 OpenAI API 호출이 필요하지만, 여기서는 기본값 반환
        return {
            "title": f"{topic} - 놓치면 후회하는 비밀!",
            "script": f"안녕하세요! 오늘은 {topic}에 대해 여러분이 꼭 알아야 할 정보를 준비했습니다. 이 영상 끝까지 보시면 정말 유용한 꿀팁을 얻으실 수 있어요! 그럼 바로 시작해볼까요?",
            "hashtags": [f"#{topic.replace(' ', '')}", "#꿀팁", "#유튜브쇼츠"]
        }
    except Exception as e:
        logger.error(f"GPT-4o 콘텐츠 생성 실패: {e}")
        return generate_fallback_content(topic)

def generate_viral_content_gemini(topic: str) -> dict:
    """Gemini를 사용하여 바이럴 콘텐츠를 생성합니다."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY가 설정되지 않았습니다.")
        return generate_fallback_content(topic)
        
    try:
        logger.info("Gemini AI에게 콘텐츠 생성을 요청합니다.")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        # 더 간단하고 명확한 프롬프트
        prompt = f"""
다음 주제로 유튜브 쇼츠용 콘텐츠를 JSON 형식으로 만들어주세요:
주제: {topic}

아래 형식으로 정확히 답변해주세요:
{{
  "title": "25자 이내의 제목",
  "script": "300자 이내의 스크립트",
  "hashtags": ["#태그1", "#태그2", "#태그3"]
}}
"""
        
        response = model.generate_content(prompt)
        cleaned_text = clean_json_response(response.text)
        content = json.loads(cleaned_text)
        
        # 필수 필드 검증
        required_fields = ['title', 'script', 'hashtags']
        if not all(key in content for key in required_fields):
            raise ValueError("필수 필드가 누락되었습니다.")
        
        logger.info("Gemini AI 콘텐츠 생성 성공!")
        return content
        
    except Exception as e:
        logger.error(f"Gemini AI 콘텐츠 생성 실패: {e}. 기본 콘텐츠를 사용합니다.")
        return generate_fallback_content(topic)

def generate_fallback_content(topic: str) -> dict:
    """기본 콘텐츠를 생성합니다."""
    return {
        "title": f"{topic} - 모르면 손해!",
        "script": f"오늘은 {topic}에 대해 아무도 몰랐던 비밀을 알려드립니다! 끝까지 보시면 깜짝 놀랄 정보가 있습니다. 지금 바로 확인해보세요!",
        "hashtags": [f"#{topic.replace(' ', '')}", "#꿀팁", "#쇼츠"]
    }

def create_simple_video(duration=15) -> str:
    """간단한 색상 배경 영상을 생성합니다."""
    logger.info("기본 색상 배경 영상을 생성합니다.")
    
    # RGB 색상값으로 변경 (16진수 문제 해결)
    colors = [
        (26, 26, 26),      # 어두운 회색
        (42, 13, 13),      # 어두운 빨강
        (13, 26, 20),      # 어두운 초록
        (14, 13, 42)       # 어두운 파랑
    ]
    
    video_path = Config.TEMP_DIR / f"default_bg_{uuid.uuid4()}.mp4"
    
    try:
        # RGB 색상으로 ColorClip 생성
        selected_color = random.choice(colors)
        clip = ColorClip(
            size=(Config.SHORTS_WIDTH, Config.SHORTS_HEIGHT),
            color=selected_color,  # RGB 튜플 사용
            duration=duration
        )
        
        clip.write_videofile(str(video_path), fps=24, logger=None, verbose=False)
        clip.close()  # 메모리 정리
        
        logger.info(f"기본 배경 영상 생성 완료: {video_path}")
        return str(video_path)
        
    except Exception as e:
        logger.error(f"기본 배경 영상 생성 실패: {e}")
        raise

def download_video_from_pexels(query: str, duration: int) -> str:
    """Pexels에서 영상을 다운로드합니다."""
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        logger.warning("PEXELS_API_KEY가 없습니다. 기본 배경 영상을 사용합니다.")
        return create_simple_video(duration)
    
    try:
        logger.info(f"Pexels에서 '{query}' 관련 영상을 검색합니다.")
        headers = {"Authorization": api_key}
        
        # 검색 쿼리 단순화 (첫 번째 단어만 사용)
        search_query = query.split()[0] if query else "business"
        url = f"https://api.pexels.com/videos/search?query={search_query}&per_page=20&orientation=portrait"
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        videos = data.get('videos', [])
        
        if not videos:
            logger.warning("검색 결과가 없습니다. 일반적인 키워드로 재시도합니다.")
            # 일반적인 키워드로 재시도
            fallback_queries = ["success", "money", "business", "lifestyle"]
            for fallback in fallback_queries:
                url = f"https://api.pexels.com/videos/search?query={fallback}&per_page=20&orientation=portrait"
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    videos = response.json().get('videos', [])
                    if videos:
                        break
        
        if not videos:
            logger.warning("모든 검색에 실패했습니다. 기본 배경을 사용합니다.")
            return create_simple_video(duration)
        
        # 적절한 해상도의 영상 선택
        selected_video = random.choice(videos)
        video_files = selected_video.get('video_files', [])
        
        # HD 화질 우선 선택
        best_video = None
        for video_file in video_files:
            if video_file.get('quality') == 'hd':
                best_video = video_file
                break
        
        if not best_video and video_files:
            best_video = video_files[0]  # 첫 번째 파일 사용
        
        if not best_video:
            logger.warning("다운로드할 영상 파일을 찾지 못했습니다.")
            return create_simple_video(duration)
        
        video_url = best_video['link']
        logger.info(f"다운로드할 영상 URL: {video_url}")
        
        # 영상 다운로드
        video_path = Config.TEMP_DIR / f"pexels_{uuid.uuid4()}.mp4"
        with requests.get(video_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        logger.info(f"Pexels 영상 다운로드 완료: {video_path}")
        return str(video_path)
        
    except Exception as e:
        logger.error(f"Pexels 영상 다운로드 실패: {e}. 기본 배경 영상을 사용합니다.")
        return create_simple_video(duration)

def generate_tts_with_elevenlabs(text: str) -> str:
    """ElevenLabs를 사용하여 TTS 음성을 생성합니다."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        logger.error("ELEVENLABS_API_KEY가 설정되지 않았습니다.")
        raise ValueError("ElevenLabs API 키가 필요합니다.")
    
    try:
        logger.info("ElevenLabs API를 사용하여 음성 생성을 시작합니다.")
        client = ElevenLabs(api_key=api_key)
        
        # 한국어 지원 음성으로 변경
        voice_id = "uyVNoMrnUku1dZyVEXwD"  # 기본 영어 음성
        
        audio_path = Config.TEMP_DIR / f"{uuid.uuid4()}.mp3"
        
        # 음성 생성
        audio = client.generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2"  # 다국어 모델 사용
        )
        
        # 파일로 저장
        with open(audio_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        
        logger.info(f"ElevenLabs 음성 저장 완료: {audio_path}")
        return str(audio_path)
        
    except Exception as e:
        logger.error(f"ElevenLabs TTS 생성 실패: {e}")
        raise

def create_shorts_video(video_path: str, audio_path: str, title: str) -> str:
    """쇼츠 영상을 생성합니다."""
    try:
        logger.info("쇼츠 영상 생성을 시작합니다.")
        
        # 비디오 클립 로드
        video = VideoFileClip(video_path)
        
        # 쇼츠 크기에 맞게 리사이즈 (세로형)
        video = video.resize(height=Config.SHORTS_HEIGHT)
        if video.w > Config.SHORTS_WIDTH:
            video = video.resize(width=Config.SHORTS_WIDTH)
        
        # 중앙 정렬
        video = video.set_position('center')
        
        # 오디오 클립 로드
        from moviepy.editor import AudioFileClip
        audio = AudioFileClip(audio_path)
        
        # 비디오 길이를 오디오 길이에 맞춤
        if video.duration < audio.duration:
            # 비디오가 짧으면 반복
            video = video.loop(duration=audio.duration)
        else:
            # 비디오가 길면 자름
            video = video.subclip(0, audio.duration)
        
        # 오디오 설정
        final_video = video.set_audio(audio)
        
        # 최종 영상 저장
        output_path = Config.OUTPUT_DIR / f"shorts_{uuid.uuid4()}.mp4"
        final_video.write_videofile(
            str(output_path),
            fps=24,
            codec='libx264',
            audio_codec='aac',
            logger=None,
            verbose=False
        )
        
        # 메모리 정리
        video.close()
        audio.close()
        final_video.close()
        
        logger.info(f"쇼츠 영상 생성 완료: {output_path}")
        return str(output_path)
        
    except Exception as e:
        logger.error(f"쇼츠 영상 생성 실패: {e}")
        raise

def estimate_audio_duration(text: str) -> int:
    """텍스트 길이로 음성 길이를 추정합니다."""
    # 한국어 기준 약 초당 3-4글자
    chars_per_second = 3.5
    estimated_duration = len(text) / chars_per_second
    return max(10, int(estimated_duration) + 2)  # 최소 10초

def cleanup_temp_files():
    """임시 파일들을 정리합니다."""
    try:
        temp_dir = Config.TEMP_DIR
        for file_path in temp_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()
        logger.info("임시 파일 정리 완료")
    except Exception as e:
        logger.warning(f"임시 파일 정리 중 오류: {e}")
