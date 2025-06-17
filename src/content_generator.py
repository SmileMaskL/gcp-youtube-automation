import google.generativeai as genai
from datetime import datetime
import random

def get_trending_topics():
    genai.configure(api_key=Config.get_api_key("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""오늘의 핫한 주제 5개를 JSON 형식으로 생성해주세요. 오늘 날짜는 {datetime.now().strftime('%Y-%m-%d')}입니다.
    [{{"title": "제목", "script": "대본", "pexel_query": "검색어"}}]"""
    
    response = model.generate_content(prompt)
    return eval(response.text)
