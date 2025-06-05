import os
import random
import logging
import requests
import json
from bs4 import BeautifulSoup
from google.cloud import secretmanager
from datetime import datetime, timedelta
import shutil

logger = logging.getLogger(__name__)

# Secret Manager 클라이언트
_secret_manager_client = None
def _get_secret_manager_client():
    global _secret_manager_client
    if _secret_manager_client is None:
        _secret_manager_client = secretmanager.SecretManagerServiceClient()
    return _secret_manager_client

def get_secret(secret_id):
    try:
        project_id = os.getenv('GCP_PROJECT_ID')
        client = _get_secret_manager_client()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        logger.error(f"비밀 불러오기 실패: {str(e)}")
        raise

# src/utils.py 트렌드 분석 강화
def get_trending_topics():
    # 실시간 인기 검색어 크롤링 추가
    trends = crawl_google_trends()
    return trends[0] if trends else "AI 기술"

def get_trending_topics():
    """다음 랭킹 뉴스에서 트렌드 토픽 수집"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}
        daum_trends = []
        try:
            res = requests.get('https://news.daum.net/ranking/popular', headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 2025년 6월 현재 다음 뉴스 구조
            for item in soup.select('ul.list_news > li > div.cont_thumb > strong > a'):
                daum_trends.append({"title": item.get_text(strip=True)})
                if len(daum_trends) >= 5:
                    break
                    
        except Exception as e:
            logger.warning(f"다음 뉴스 크롤링 실패: {str(e)}")
            
        if daum_trends:
            logger.info(f"📰 다음 뉴스에서 {len(daum_trends)}개 트렌드 토픽 수집")
            return daum_trends
        
        # 백업 주제
        backup_topics = [
            {"title": "AI 기술 동향 2025"},
            {"title": "주식 시장 최신 분석"},
            {"title": "건강 관리 필수 팁"},
            {"title": "디지털 마케팅 전략"},
            {"title": "유튜브 수익 증대 방법"}
        ]
        return backup_topics[:3]
        
    except Exception as e:
        logger.error(f"트렌드 토픽 수집 실패: {str(e)}")
        return [{"title": "AI 기술 동향 2025"}]

# API 키 로테이션 시스템
_last_api_key_index = -1
_api_keys = {}

def rotate_api_key():
    global _last_api_key_index, _api_keys
    
    if not _api_keys:
        try:
            # OpenAI API 키
            openai_keys_str = get_secret("OPENAI_API_KEYS")
            openai_keys = [k.strip() for k in openai_keys_str.split(',') if k.strip()]
            if openai_keys:
                _api_keys['openai'] = openai_keys
            
            # Gemini API 키
            gemini_key = get_secret("GEMINI_API_KEY")
            if gemini_key:
                _api_keys['gemini'] = gemini_key
                
        except Exception as e:
            logger.error(f"API 키 로드 실패: {str(e)}")
    
    available_ais = []
    if 'openai' in _api_keys and _api_keys['openai']:
        available_ais.extend([{"OPENAI_API_KEY": k} for k in _api_keys['openai']])
    if 'gemini' in _api_keys and _api_keys['gemini']:
        available_ais.append({"GEMINI_API_KEY": _api_keys['gemini']})
    
    if not available_ais:
        raise ValueError("사용 가능한 API 키 없음")
    
    _last_api_key_index = (_last_api_key_index + 1) % len(available_ais)
    return available_ais[_last_api_key_index]

def clean_old_data():
    """오래된 데이터 정리"""
    logger.info("🧹 데이터 정리 시작")
    
    # 로그 파일 정리 (7일 이상)
    logs_dir = "logs"
    if os.path.exists(logs_dir):
        for filename in os.listdir(logs_dir):
            file_path = os.path.join(logs_dir, filename)
            if os.path.isfile(file_path):
                file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_age.days > 7:
                    os.remove(file_path)
                    logger.info(f"🗑️ 오래된 로그 삭제: {filename}")
    
    # 출력 파일 정리 (1일 이상)
    output_dir = "output"
    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            if os.path.isfile(file_path):
                file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_age.days > 1:
                    os.remove(file_path)
                    logger.info(f"🗑️ 오래된 출력 파일 삭제: {filename}")
    
    logger.info("🧹 데이터 정리 완료")
