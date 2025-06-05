import os
import random
import logging
import requests
import json # json 임포트 추가
from bs4 import BeautifulSoup
from google.cloud import secretmanager
from datetime import datetime, timedelta # 데이터 정리 위한 임포트
import shutil # 폴더 삭제를 위한 임포트

logger = logging.getLogger(__name__)

# Secret Manager 클라이언트 전역으로 초기화 (최초 1회만)
_secret_manager_client = None
def _get_secret_manager_client():
    global _secret_manager_client
    if _secret_manager_client is None:
        _secret_manager_client = secretmanager.SecretManagerServiceClient()
    return _secret_manager_client

def get_secret(secret_id):
    """GCP Secret Manager에서 비밀 값 가져오기"""
    try:
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            logger.error("GCP_PROJECT_ID 환경 변수가 설정되지 않았습니다.")
            raise ValueError("GCP_PROJECT_ID 환경 변수 미설정")
            
        client = _get_secret_manager_client()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        logger.error(f"비밀 불러오기 실패 (Secret ID: {secret_id}): {str(e)}\n{traceback.format_exc()}")
        raise # 비밀을 가져오지 못하면 치명적이므로 예외를 다시 발생

def get_trending_topics():
    """네이버 실시간 검색어 + 백업 주제를 통해 트렌드 토픽 가져오기"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        # 네이버 실시간 검색어는 현재 제공되지 않으므로, 뉴스 트렌드 또는 구글 트렌드로 대체
        # 여기서는 간단히 '오늘의 주요 뉴스'와 같은 주제를 활용하는 방식으로 대체
        # 실제 네이버 뉴스 트렌드 크롤링은 복잡하므로, 안정적인 키워드 제공을 위해 대체 키워드 활용
        
        # 구글 트렌드 API 또는 웹 크롤링 (좀 더 복잡)
        # 현재는 한국 뉴스 사이트의 '가장 많이 본 뉴스' 등을 크롤링하는 것이 현실적
        # 예시: 다음(Daum) 뉴스 랭킹 크롤링 (불안정할 수 있음)
        daum_trends = []
        try:
            res = requests.get('https://media.daum.net/ranking/kakaotv', headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            # 클래스 이름은 Daum 웹사이트 변경에 따라 달라질 수 있습니다.
            # 예시: <a> 태그의 text로 가져오기
            for item in soup.select('ul.list_newsrank li a.link_txt'):
                daum_trends.append({"title": item.get_text(strip=True)})
                if len(daum_trends) >= 5: # 상위 5개만 가져오기
                    break
        except Exception as daum_e:
            logger.warning(f"Daum 뉴스 랭킹 크롤링 실패: {daum_e}. 백업 주제 사용.")

        if daum_trends:
            logger.info(f"📰 Daum 뉴스 랭킹에서 {len(daum_trends)}개 트렌드 토픽 발견.")
            return daum_trends
        
        # 백업 주제
        backup_topics = [
            {"title": "최신 인공지능 기술 동향"},
            {"title": "주식 시장 분석"},
            {"title": "건강 관리 팁"},
            {"title": "경제 위기 대응 전략"},
            {"title": "유튜브 수익 창출 노하우"}
        ]
        logger.info("백업 주제 사용.")
        return [{"title": random.choice(backup_topics)['title']}] # 리스트 형태로 반환

    except requests.exceptions.RequestException as req_e:
        logger.error(f"트렌드 토픽 요청 실패: {req_e}. 백업 주제 사용.")
        return [{"title": random.choice(["AI 기술", "주식 투자", "건강 관리"])}]
    except Exception as e:
        logger.error(f"트렌드 토픽 가져오기 실패: {str(e)}\n{traceback.format_exc()}. 백업 주제 사용.")
        return [{"title": random.choice(["AI 기술", "주식 투자", "건강 관리"])}]


_last_api_key_index = -1
_api_keys = {} # AI API 키를 저장할 딕셔너리 (초기화 시 Secret Manager에서 로드)

def rotate_api_key():
    """
    OpenAI API 키 (10개)와 Google Gemini API 키를 로테이션으로 번갈아 사용합니다.
    사용 시점에 Secret Manager에서 키를 로드합니다.
    """
    global _last_api_key_index, _api_keys

    if not _api_keys: # 딕셔너리가 비어있으면 Secret Manager에서 로드
        try:
            # OpenAI API 키 로드
            openai_keys_str = get_secret("OPENAI_API_KEYS")
            openai_keys = [k.strip() for k in openai_keys_str.split(',') if k.strip()]
            if openai_keys:
                _api_keys['openai'] = openai_keys
                logger.info(f"OpenAI API 키 {len(openai_keys)}개 로드 완료.")
            else:
                logger.warning("OPENAI_API_KEYS Secret Manager에서 키를 찾을 수 없습니다.")

            # Gemini API 키 로드
            gemini_key = get_secret("GEMINI_API_KEY")
            if gemini_key:
                _api_keys['gemini'] = gemini_key
                logger.info("Gemini API 키 로드 완료.")
            else:
                logger.warning("GEMINI_API_KEY Secret Manager에서 키를 찾을 수 없습니다.")

        except Exception as e:
            logger.error(f"API 키 로드 실패: {e}")
            raise # 키 로드 실패는 치명적이므로 예외 발생

    available_ais = []
    if 'openai' in _api_keys and _api_keys['openai']:
        available_ais.extend([{"OPENAI_API_KEY": k} for k in _api_keys['openai']])
    if 'gemini' in _api_keys and _api_keys['gemini']:
        available_ais.append({"GEMINI_API_KEY": _api_keys['gemini']})

    if not available_ais:
        raise ValueError("사용 가능한 AI API 키가 없습니다. Secret Manager 설정을 확인해주세요.")

    _last_api_key_index = (_last_api_key_index + 1) % len(available_ais)
    selected_key_info = available_ais[_last_api_key_index]
    
    if "OPENAI_API_KEY" in selected_key_info:
        logger.info(f"🌐 OpenAI API 키 사용. 인덱스: {_last_api_key_index % len(_api_keys.get('openai', [1]))}")
    elif "GEMINI_API_KEY" in selected_key_info:
        logger.info("🌐 Google Gemini API 키 사용.")
        
    return selected_key_info


def clean_old_data():
    """
    오래된 로그 파일, 수익 로그 파일, 임시 파일 등을 정리하여 용량을 관리합니다.
    일주일(7일)이 지난 데이터를 삭제합니다.
    """
    logger.info("데이터 정리 작업을 시작합니다.")
    
    # 1. logs 폴더 정리
    logs_dir = "logs"
    if os.path.exists(logs_dir):
        for filename in os.listdir(logs_dir):
            file_path = os.path.join(logs_dir, filename)
            if os.path.isfile(file_path):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if datetime.now() - file_mtime > timedelta(days=7):
                    try:
                        os.remove(file_path)
                        logger.info(f"🗑️ 오래된 로그 파일 삭제: {file_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ 로그 파일 삭제 실패 ({file_path}): {e}")

    # 2. revenue_log.csv 정리 (선택 사항: 파일이 너무 커지면 로직 추가)
    # 현재는 단순 추가 방식이므로 파일 크기가 커지면 직접 관리 필요
    # 또는, 일정 크기 이상이면 백업 후 새로 시작하는 로직 구현 가능

    # 3. output 폴더 정리 (생성된 영상 파일)
    output_dir = "output"
    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            if os.path.isfile(file_path):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if datetime.now() - file_mtime > timedelta(days=1): # 하루 지난 영상 파일은 삭제
                    try:
                        os.remove(file_path)
                        logger.info(f"🗑️ 오래된 출력 영상 파일 삭제: {file_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ 출력 영상 파일 삭제 실패 ({file_path}): {e}")
            elif os.path.isdir(file_path): # output 폴더 내 하위 폴더 (임시 파일용)
                dir_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if datetime.now() - dir_mtime > timedelta(days=1):
                    try:
                        shutil.rmtree(file_path)
                        logger.info(f"��️ 오래된 출력 폴더 삭제: {file_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ 출력 폴더 삭제 실패 ({file_path}): {e}")
    
    # 4. 임시 파일 디렉토리 정리 (tempfile.mkdtemp()로 생성된 디렉토리)
    # app.py의 finally 블록에서 개별적으로 삭제되므로 여기서 추가적인 처리는 불필요

    logger.info("데이터 정리 작업 완료.")
