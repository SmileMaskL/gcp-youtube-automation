"""
수익 최적화 유튜브 자동화 유틸리티 (완전한 버전)
- 최종 수정: 2025년 6월 15일
- 주요 개선: 들여쓰기 오류 수정, 무료 AI 모델(Gemini 1.5 Flash) 적용, 수익화 로직 및 안정성 강화
"""

import os
import requests
import json
import logging
import time
import uuid
import random
from pathlib import Path
from moviepy.editor import *
from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
import google.generativeai as genai

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# 진행 상황을 쉽게 추적할 수 있도록 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== 핵심 기능 (수익화 및 안정성 강화) ====================

def text_to_speech(text: str, output_path: str = "output/audio.mp3") -> str:
    """
    안정성과 표현력을 높인 텍스트 음성 변환(TTS) 함수.
    ElevenLabs API를 사용하여 자연스러운 음성을 생성합니다.
    """
    logger.info("음성 생성을 시작합니다...")
    try:
        # 1. API 키 확인 (가장 먼저!)
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("환경 변수에서 ELEVENLABS_API_KEY를 찾을 수 없습니다.")

        # 2. ElevenLabs 클라이언트 초기화 (들여쓰기 오류 완벽 수정)
        client = ElevenLabs(api_key=api_key)

        # 3. 음성 생성 (매력적인 목소리 설정으로 청취자 몰입감 극대화)
        audio = client.generate(
            text=text,
            voice=Voice(
                voice_id='Rachel',  # 인기가 많고 신뢰감을 주는 목소리
                settings=VoiceSettings(stability=0.5, similarity_boost=0.75, style=0.0, use_speaker_boost=True)
            ),
            model="eleven_multilingual_v2"  # 최신 다국어 모델 사용
        )

        # 4. 생성된 오디오 파일 저장 (디렉토리 자동 생성)
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(audio)
        
        logger.info(f"음성 파일이 성공적으로 '{output_path}'에 저장되었습니다.")
        return output_path

    except Exception as e:
        logger.error(f"ElevenLabs 음성 생성 중 오류 발생: {e}")
        # API 실패 시, 영상 제작이 멈추지 않도록 무음 오디오를 생성하는 비상 대책
        duration = len(text.split()) * 0.5
        silent_audio = AudioClip(lambda t: 0, duration=max(1.0, duration), fps=22050)
        
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        silent_audio.write_audiofile(output_path, fps=22050, logger=None)
        logger.warning(f"비상 대책으로 '{output_path}'에 무음 오디오를 생성했습니다.")
        return output_path

def download_video_from_pexels(query: str = None) -> str:
    """
    수익성 높은 주제의 영상을 Pexels에서 다운로드 (네트워크 오류 대비 재시도 기능 추가)
    """
    logger.info(f"'{query or "수익형 키워드"}' 관련 영상 다운로드를 시작합니다...")
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        logger.warning("PEXELS_API_KEY가 없습니다. 기본 단색 배경 영상을 생성합니다.")
        return create_simple_video()

    # 수익화에 유리하고 시청자 참여를 유도하는 키워드 목록
    money_keywords = [
        "luxury", "success", "motivation", "business", "travel", "finance",
        "investment", "technology", "future", "city night", "nature abstract"
    ]
    search_query = query or random.choice(money_keywords)

    headers = {"Authorization": api_key}
    # 쇼츠에 적합하도록 세로 영상(portrait)만 검색
    url = f"https://api.pexels.com/videos/search?query={search_query}&per_page=15&orientation=portrait"

    for attempt in range(3):  # 최대 3번 재시도
        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()

            videos = response.json().get("videos", [])
            if not videos:
                logger.warning(f"'{search_query}'에 대한 영상 결과가 없습니다. 다른 키워드로 시도합니다.")
                search_query = random.choice(money_keywords)
                continue

            # 충분한 길이를 가진 영상 필터링
            long_enough_videos = [v for v in videos if v.get('duration', 0) > 15]
            if not long_enough_videos:
                logger.warning("15초 이상인 영상을 찾지 못했습니다. 기본 영상을 생성합니다.")
                return create_simple_video()
            
            # 그중에서 랜덤으로 하나 선택하여 매번 다른 영상이 나오게 함
            video = random.choice(long_enough_videos)
            video_file = random.choice(video['video_files'])['link']

            # 임시 저장 경로 설정
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            temp_path = temp_dir / f"{uuid.uuid4()}.mp4"

            logger.info(f"영상 다운로드 중... (시도 {attempt + 1})")
            with requests.get(video_file, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(temp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            logger.info(f"영상이 성공적으로 '{temp_path}'에 다운로드되었습니다.")
            return str(temp_path)

        except requests.exceptions.RequestException as e:
            logger.error(f"Pexels 영상 다운로드 오류 (시도 {attempt + 1}/3): {e}")
            time.sleep(3)

    logger.error("반복적인 오류로 Pexels 영상 다운로드에 실패했습니다. 기본 영상을 생성합니다.")
    return create_simple_video()

def create_simple_video(duration: int = 60) -> str:
    """API 사용 불가 시, 시선을 끄는 단색 배경의 비상용 영상을 생성합니다."""
    logger.info("기본 배경 영상을 생성합니다.")
    try:
        colors = ["#1e3c72", "#2a5298", "#434343", "#000000"]
        clip = ColorClip(size=(1080, 1920), color=random.choice(colors), duration=duration)

        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / f"{uuid.uuid4()}.mp4"
        
        clip.write_videofile(str(temp_path), fps=24, logger=None)
        
        logger.info(f"기본 영상이 '{temp_path}'에 생성되었습니다.")
        return str(temp_path)
    except Exception as e:
        logger.critical(f"기본 영상 생성 중 치명적 오류 발생: {e}")
        raise

def add_text_to_clip(video_path: str, script: str, output_path: str) -> str:
    """가독성과 클릭률을 극대화한 스타일로 영상에 자막을 추가합니다."""
    logger.info("영상에 자막을 추가하는 중입니다...")
    try:
        video = VideoFileClip(video_path)

        # 가독성이 매우 높은 자막 스타일 (GCP 환경에서도 잘 동작하는 기본 폰트 사용)
        text_clip = TextClip(
            script,
            fontsize=75,
            color='white',
            font='Arial-Bold',  # 기본 폰트로 변경하여 호환성 문제 해결
            stroke_color='black',
            stroke_width=2.5,
            method='caption',
            size=(video.w * 0.9, None),
            align='center'
        ).set_position(('center', 'center')).set_duration(video.duration)

        final_video = CompositeVideoClip([video, text_clip])
        final_video.write_videofile(output_path, codec='libx264', audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True, logger=None)

        video.close()
        final_video.close()
        
        logger.info(f"자막이 추가된 최종 영상이 '{output_path}'에 저장되었습니다.")
        return output_path
    except Exception as e:
        logger.error(f"영상에 텍스트 추가 실패: {e}. 원본 영상을 그대로 반환합니다.")
        return video_path

# ==================== 콘텐츠 생성 (Gemini 1.5 Flash 무료 모델 활용) ====================

def generate_viral_content(topic: str) -> dict:
    """
    Google Gemini 1.5 Flash 모델을 사용하여 바이럴 쇼츠 콘텐츠를 생성합니다.
    (비용 효율적이고 빠르며 강력함)
    """
    logger.info(f"'{topic}' 주제로 바이럴 콘텐츠 생성을 시작합니다...")
    try:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
            
        genai.configure(api_key=gemini_api_key)
        
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        # 수익화에 초점을 맞춘 강력한 프롬프트
        prompt = f"""
        당신은 100만 유튜버를 만든 바이럴 쇼츠 콘텐츠 전문 작가입니다.
        아래 주제에 대해 시청자가 끝까지 보게 만들고, '좋아요'와 '구독'을 누를 수밖에 없는 60초 분량의 유튜브 쇼츠 콘텐츠를 생성해주세요.

        **주제: {topic}**

        **필수 조건:**
        1.  **훅 (Hook, 첫 3초):** 시청자의 스크롤을 즉시 멈출 강력한 한 문장으로 시작하세요. (질문, 충격적인 사실, 일반적인 통념 뒤집기)
        2.  **본문 (Body):** 핵심 내용을 2~3가지로 나누어 빠르고 흥미롭게 설명하세요. 각 문장은 짧고 명확하게 작성해주세요.
        3.  **결론 (Conclusion):** 행동을 유도하는 문구(Call to Action)를 포함하여 마무리하세요. (예: "더 많은 꿀팁은 구독!", "여러분의 생각은 댓글로...")
        4.  **스타일:** 친근하지만 신뢰감 있는 말투를 사용하세요.

        **출력 형식 (반드시 JSON 형식만 출력):**
        {{
            "title": "클릭을 유발하는 25자 내외의 제목",
            "script": "훅, 본문, 결론을 포함한 350자 내외의 완벽한 대본",
            "hashtags": ["#핵심키워드", "#관련토픽", "#바이럴", "#꿀팁", "#shorts"]
        }}
        """

        response = model.generate_content(prompt)
        
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        content = json.loads(cleaned_response)
        
        logger.info("Gemini 콘텐츠 생성이 성공적으로 완료되었습니다.")
        return content

    except Exception as e:
        logger.error(f"Gemini 콘텐츠 생성 실패: {e}. 비상용 기본 콘텐츠를 사용합니다.")
        return {
            "title": f"몰랐으면 손해! {topic}의 모든 것",
            "script": f"혹시 {topic}에 대해 얼마나 아시나요? 대부분이 모르는 3가지 비밀을 지금부터 알려드릴게요. 첫째,... 둘째,... 마지막으로 가장 중요한 셋째는... 이 정보가 유용했다면 구독과 좋아요 잊지 마세요!",
            "hashtags": [f"#{''.join(filter(str.isalnum, topic))}", "#꿀팁", "#자기계발", "#성공", "#shorts"]
        }

# ==================== 설정 및 유틸리티 ====================

def check_requirements():
    """스크립트 실행에 필요한 필수 환경 변수가 설정되었는지 확인합니다."""
    logger.info("필수 환경 변수 설정을 확인합니다...")
    required_keys = ["ELEVENLABS_API_KEY", "PEXELS_API_KEY", "GEMINI_API_KEY"]
    all_set = True
    for key in required_keys:
        if not os.getenv(key):
            logger.warning(f"[경고] 필수 환경 변수 '{key}'가 설정되지 않았습니다. 관련 기능이 제한될 수 있습니다.")
            all_set = False
    if all_set:
        logger.info("모든 필수 환경 변수가 성공적으로 설정되었습니다.")

if __name__ == "__main__":
    logger.info("utils.py 스크립트를 직접 실행하여 기본 기능을 테스트합니다.")
    check_requirements()
    
    test_topic = "성공하는 사람들의 아침 습관"
    generated_content = generate_viral_content(test_topic)
    
    print("\n--- 생성된 콘텐츠 테스트 ---")
    print(json.dumps(generated_content, indent=2, ensure_ascii=False))

    if os.getenv("ELEVENLABS_API_KEY") and generated_content:
        text_to_speech(generated_content['script'], "output/test_audio.mp3")
    
    if os.getenv("PEXELS_API_KEY"):
        download_video_from_pexels(test_topic)
        
    print("\n테스트 완료.")
