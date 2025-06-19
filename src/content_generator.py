from src.ai_rotation import ai_rotation_manager
from src.monitoring import log_system_health
from pytrends.request import TrendReq
import datetime
import random
import requests
import os

def get_trending_topic(country_code='KR', max_retries=3):
    """Google Trends에서 오늘의 인기 토픽을 가져옵니다."""
    pytrends = TrendReq(hl='ko', tz=540) # 한국 시간대
    for attempt in range(max_retries):
        try:
            trending_searches_df = pytrends.trending_searches(pn=country_code)
            if not trending_searches_df.empty:
                # 인기 검색어 목록에서 랜덤으로 하나 선택
                topic = trending_searches_df.iloc[random.randint(0, len(trending_searches_df) - 1)]['title']
                log_system_health(f"Google Trends에서 트렌드 토픽 '{topic}'을 가져왔습니다.", level="info")
                return topic
            else:
                log_system_health(f"Google Trends에서 인기 토픽을 찾을 수 없습니다. (시도 {attempt + 1})", level="warning")
        except Exception as e:
            log_system_health(f"Google Trends API 호출 오류: {e}. (시도 {attempt + 1})", level="error")
        if attempt < max_retries - 1:
            import time
            time.sleep(2 ** attempt) # Exponential backoff
    log_system_health("Google Trends에서 트렌드 토픽을 가져오지 못했습니다. 기본값 사용.", level="error")
    return "자연" # 기본값

def generate_video_script(topic):
    """AI를 사용하여 영상 스크립트를 생성합니다."""
    prompt = f"""
    당신은 인기 있는 YouTube Shorts 영상 스크립트 작성 전문가입니다.
    주어진 주제에 대해 60초 길이의 매력적인 YouTube Shorts 영상 스크립트를 작성해주세요.
    다음 지침을 엄격히 따르십시오:

    1.  **길이:** 60초 분량에 딱 맞게 스크립트를 작성합니다. (약 150-180단어)
    2.  **구조:**
        * **강력한 후크(Hook):** 시작 5초 이내에 시청자의 시선을 사로잡는 문장.
        * **핵심 내용:** 주제에 대한 흥미로운 사실, 팁 또는 이야기.
        * **클로징:** 시청자에게 좋아요, 구독, 댓글을 유도하는 Call-to-Action.
    3.  **스타일:** 빠르고 간결하며, 시청자의 호기심을 자극하는 말투. 유튜브 쇼츠에 적합한 캐주얼하고 대화적인 톤.
    4.  **내용:** 항상 최신 정보와 흥미로운 사실에 기반하여, 정보 전달과 재미를 동시에 추구합니다.
    5.  **예시:**
        ```
        [Hook] 💡 잠깐! 당신이 몰랐던 놀라운 사실! 오늘 밤 하늘을 보면...
        [Main Content] 혹시 그거 아셨나요? 최근 연구에 따르면 지구의 자전 속도가... (이어서 흥미로운 사실 나열)
        [Call to Action] 😱 더 많은 놀라운 사실을 놓치지 않으려면 지금 바로 구독하고 알림을 켜세요! 좋아요와 댓글도 잊지 마세요!
        ```
    6.  **출력 형식:** 오직 스크립트 내용만 반환하고, 다른 서론/결론/주석은 일절 포함하지 않습니다.

    주제: "{topic}"
    """
    try:
        script = ai_rotation_manager.generate_content(prompt, max_tokens=300) # 스크립트 길이를 위해 토큰 늘림
        log_system_health(f"주제 '{topic}'에 대한 스크립트가 성공적으로 생성되었습니다.", level="info")
        return script
    except Exception as e:
        log_system_health(f"스크립트 생성 중 오류 발생: {e}", level="error")
        return "스크립트를 생성할 수 없습니다."

def generate_video_title(script, topic):
    """AI를 사용하여 영상 제목을 생성합니다."""
    prompt = f"""
    다음 YouTube Shorts 영상 스크립트와 주제를 바탕으로, 클릭을 유도하고 검색에 최적화된 매력적인 한국어 제목을 20자 이내로 1개만 제안해주세요.
    반드시 제목만 반환하고, 다른 서론/결론/주석은 일절 포함하지 마세요.
    이모지나 특수문자를 적절히 활용하여 시선을 사로잡으세요.

    스크립트:
    {script}

    주제: {topic}
    """
    try:
        title = ai_rotation_manager.generate_content(prompt, max_tokens=50)
        log_system_health(f"영상 제목이 성공적으로 생성되었습니다: {title}", level="info")
        return title.strip()
    except Exception as e:
        log_system_health(f"제목 생성 중 오류 발생: {e}", level="error")
        return f"오늘의 {topic} 쇼츠"

def generate_video_description(script, title, topic):
    """AI를 사용하여 영상 설명을 생성합니다."""
    prompt = f"""
    다음 YouTube Shorts 영상 스크립트, 제목, 주제를 바탕으로 시청자들이 궁금해할 만한 내용을 포함하고, 관련 해시태그를 5-10개 포함하는 한국어 영상 설명을 작성해주세요.
    길이는 100~200자 이내로 작성합니다. 유튜브 정책을 준수하고, 저작권 문제가 발생하지 않도록 일반적인 정보를 바탕으로 설명합니다.

    스크립트:
    {script}

    제목: {title}

    주제: {topic}
    """
    try:
        description = ai_rotation_manager.generate_content(prompt, max_tokens=300)
        log_system_health(f"영상 설명이 성공적으로 생성되었습니다: {description}", level="info")
        return description.strip()
    except Exception as e:
        log_system_health(f"설명 생성 중 오류 발생: {e}", level="error")
        return f"오늘의 쇼츠입니다! #{topic} #쇼츠 #유튜브쇼츠"

def generate_video_tags(topic, title):
    """AI를 사용하여 영상 태그를 생성합니다."""
    prompt = f"""
    다음 YouTube Shorts 영상 제목과 주제를 바탕으로, 검색 최적화를 위한 콤마(,)로 구분된 한국어 태그 10~15개를 생성해주세요.
    태그는 오직 콤마로 구분된 리스트 형식으로만 반환합니다. 다른 서론/결론/주석은 일절 포함하지 마세요.

    제목: {title}
    주제: {topic}
    """
    try:
        tags = ai_rotation_manager.generate_content(prompt, max_tokens=100)
        log_system_health(f"영상 태그가 성공적으로 생성되었습니다: {tags}", level="info")
        return [tag.strip() for tag in tags.split(',') if tag.strip()]
    except Exception as e:
        log_system_health(f"태그 생성 중 오류 발생: {e}", level="error")
        return [topic, "쇼츠", "유튜브쇼츠"]

def generate_youtube_comments(video_title, num_comments=3):
    """AI를 사용하여 유튜브 댓글을 자동으로 생성합니다."""
    comments = []
    for i in range(num_comments):
        prompt = f"""
        '{video_title}' 영상에 달릴 법한 긍정적이고 흥미로운 한국어 유튜브 댓글을 1개만 작성해주세요.
        댓글은 짧고 간결하며, 시청자의 호기심을 자극하거나 공감을 얻을 수 있는 내용이어야 합니다.
        이모지를 적절히 사용해주세요.
        오직 댓글 내용만 반환하고, 다른 서론/결론/주석은 일절 포함하지 마세요.
        """
        try:
            comment = ai_rotation_manager.generate_content(prompt, max_tokens=50, temperature=0.8)
            comments.append(comment.strip())
            log_system_health(f"유튜브 댓글 {i+1}이 성공적으로 생성되었습니다.", level="info")
        except Exception as e:
            log_system_health(f"유튜브 댓글 생성 중 오류 발생: {e}", level="error")
            comments.append("흥미로운 영상이네요!")
    return comments

def generate_short_summary(script):
    """영상 스크립트에서 짧은 요약을 추출합니다. (썸네일 텍스트용)"""
    prompt = f"""
    다음 영상 스크립트의 핵심 내용을 가장 잘 나타내는 짧고 강력한 문장 1개를 15자 이내로 요약해주세요.
    이 문장은 영상 썸네일에 들어갈 텍스트입니다.
    오직 요약된 문장만 반환하고, 다른 서론/결론/주석은 일절 포함하지 마세요.

    스크립트:
    {script}
    """
    try:
        summary = ai_rotation_manager.generate_content(prompt, max_tokens=30)
        log_system_health(f"썸네일 요약 텍스트가 성공적으로 생성되었습니다: {summary}", level="info")
        return summary.strip()
    except Exception as e:
        log_system_health(f"썸네일 요약 텍스트 생성 중 오류 발생: {e}", level="error")
        return "오늘의 놀라운 사실"
