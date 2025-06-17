import os
import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import Config
import logging
from retrying import retry

logger = logging.getLogger(__name__)

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def upload_to_youtube(video_path, title):
    """YouTube에 업로드"""
    try:
        # 서비스 계정 자격 증명 (GCP 서비스 계정 키 파일 경로)
        creds = None
        # 환경 변수에서 서비스 계정 키를 JSON 문자열로 가져옵니다.
        service_account_info = json.loads(os.environ['YOUTUBE_CREDENTIALS'])
        creds = service_account.Credentials.from_service_account_info(service_account_info)
        
        youtube = build('youtube', 'v3', credentials=creds)
        
        request_body = {
            'snippet': {
                'title': title,
                'description': '자동 생성된 YouTube Shorts입니다.',
                'categoryId': '22'  # Entertainment
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part='snippet,status',
            body=request_body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"업로드 진행: {int(status.progress() * 100)}%")
        
        logger.info(f"업로드 완료: {response['id']}")
        return True
    except Exception as e:
        logger.error(f"업로드 실패: {e}")
        return False
