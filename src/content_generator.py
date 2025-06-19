import os
import random
import google.generativeai as genai
import openai
from datetime import datetime

def get_trending_topics():
    # 실제 트렌드 API 연동 코드
    return ["최신 기술", "AI 동향", "주식 시장"]

def generate_content():
    # API 키 로테이션
    apis = [
        {"type": "gemini", "key": os.getenv("GEMINI_API_KEY1")},
        {"type": "gpt", "key": os.getenv("OPENAI_API_KEY1")}
    ]
    
    selected = random.choice(apis)
    topics = get_trending_topics()
    
    try:
        if selected["type"] == "gemini":
            genai.configure(api_key=selected["key"])
            model = genai.GenerativeModel('gemini-1.0-pro')
            response = model.generate_content(
                f"{datetime.today().strftime('%Y-%m-%d')} {random.choice(topics)}에 대한 유튜브 스크립트 생성해줘"
            )
            content = response.text
        else:
            openai.api_key = selected["key"]
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"{random.choice(topics)} 주제로 영상 대본 생성"}]
            )
            content = response.choices[0].message.content
            
        return {
            "title": f"{datetime.today().strftime('%m월 %d일')} {content[:30]}...",
            "script": content,
            "keywords": topics,
            "video_query": f"{random.choice(topics)} 배경 영상"
        }
    except Exception as e:
        logger.error(f"콘텐츠 생성 실패: {str(e)}")
        return default_content()

def default_content():
    return {
        "title": "오늘의 핫 이슈",
        "script": "최신 트렌드를 따라가는 내용...",
        "keywords": ["트렌드", "뉴스"],
        "video_query": "abstract background"
    }
