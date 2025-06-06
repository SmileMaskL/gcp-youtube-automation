import os
import json
import time
import logging
import traceback
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from .utils import get_secret

logger = logging.getLogger(__name__)

def is_channel_monetized(youtube):
    """채널 수익화 상태 확인"""
    try:
        response = youtube.channels().list(
            part='monetizationDetails',
            mine=True
        ).execute()
        
        if 'items' in response and response['items']:
            monetization = response['items'][0].get('monetizationDetails', {})
            return monetization.get('status', '') == 'MONETIZED'
    except Exception as e:
        logger.error(f"🔴 수익화 상태 확인 실패: {str(e)}")
    return False

def upload_video(file_path, title, description, thumbnail_path=None):
    """실전용 업로드 (수익화 자동 설정 포함)"""
    # 1. 인증 시도
    credentials = None
    try:
        # 서비스 계정 인증 시도
        service_account_json = json.loads(get_secret("GCP_SERVICE_ACCOUNT_KEY"))
        credentials = service_account.Credentials.from_service_account_info(
            service_account_json,
            scopes=['https://www.googleapis.com/auth/youtube.upload']
        )
        logger.info("✅ 서비스 계정 인증 사용")
    except Exception as sa_error:
        logger.warning(f"⚠️ 서비스 계정 실패: {sa_error}. OAuth로 전환")
        try:
            # OAuth 인증 로직
            refresh_token = get_secret("YOUTUBE_REFRESH_TOKEN")
            client_secret = get_secret("YOUTUBE_CLIENT_SECRET")
            
            # OAuth 토큰 갱신 로직 (실제 구현 필요)
            # ... [기존 refresh token 처리 코드] ...
            # credentials = 갱신된 OAuth 자격 증명
        except Exception as oauth_error:
            logger.error(f"🔴 OAuth 인증 실패: {oauth_error}")
            raise RuntimeError("모든 인증 수단 실패")

    # 2. 업로드 실행
    youtube = build('youtube', 'v3', credentials=credentials)
    for attempt in range(3):
        try:
            # 메타데이터 설정
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': ['AI자동생성', 'Shorts', '수익창출'],
                    'categoryId': '22',
                    'defaultLanguage': 'ko'
                },
                'status': {
                    'privacyStatus': 'public',
                    'publishAt': (datetime.now() + timedelta(minutes=10)).isoformat() + "Z",
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # 미디어 파일 업로드
            media = MediaFileUpload(file_path, resumable=True)
            request = youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            # 업로드 진행 모니터링
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"진행률: {int(status.progress() * 100)}%")
            
            video_id = response['id']
            logger.info(f"✅ 업로드 성공! 영상 ID: {video_id}")
            
            # 3. 썸네일 업로드
            if thumbnail_path and os.path.exists(thumbnail_path):
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                logger.info(f"🖼️ 썸네일 업로드 완료")
            
            # 4. 수익화 자동 설정 (채널 승인된 경우)
            try:
                if is_channel_monetized(youtube):
                    monetization_body = {
                        'id': video_id,
                        'monetizationDetails': {
                            'access': {
                                'allowed': True
                            }
                        }
                    }
                    youtube.videos().update(
                        part='monetizationDetails',
                        body=monetization_body
                    ).execute()
                    logger.info("💰 수익화 설정 완료!")
                else:
                    logger.warning("⚠️ 채널 수익화 미승인 상태 - 수동 설정 필요")
            except Exception as monetization_error:
                logger.error(f"🔴 수익화 설정 실패: {str(monetization_error)}")
            
            return f"https://www.youtube.com/watch?v={video_id}"
            
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                wait_time = 2 ** attempt
                logger.warning(f"🔄 서버 오류 ({e.resp.status}), {wait_time}초 후 재시도...")
                time.sleep(wait_time)
            else:
                error_details = json.loads(e.content).get('error', {})
                logger.error(f"🔴 치명적 오류: {error_details.get('message', 'Unknown')}")
                raise
        except Exception as e:
            logger.error(f"🔴 업로드 실패: {str(e)}\n{traceback.format_exc()}")
            if attempt == 2:
                raise RuntimeError("업로드 3회 연속 실패")
            time.sleep(3)
    
    return None
