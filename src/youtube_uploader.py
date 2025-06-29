# src/youtube_uploader.py

import os
import logging
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# YouTube API 스코프
# 'https://www.googleapis.com/auth/youtube.upload'는 동영상 업로드 권한,
# 'https://www.googleapis.com/auth/youtube.force-ssl'은 HTTPS를 강제하여 보안을 강화합니다.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.force-ssl']

def get_authenticated_service(client_id, client_secret, refresh_token):
    """
    제공된 클라이언트 ID, 시크릿, 새로고침 토큰을 사용하여
    YouTube Data API 서비스 객체를 반환합니다.
    새로고침 토큰으로 액세스 토큰을 자동으로 갱신합니다.
    """
    logger.info("YouTube API 서비스 인증 시도 중...")
    
    creds = Credentials(
        token=None,  # 초기 액세스 토큰은 없어도 됨 (refresh_token으로 갱신)
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES
    )

    try:
        # 새로고침 토큰을 사용하여 액세스 토큰 갱신 시도
        creds.refresh(Request())
        logger.info("✅ YouTube API 자격 증명 성공적으로 갱신됨.")
    except Exception as e:
        logger.error(f"❌ YouTube 자격 증명 갱신 실패: {e}", exc_info=True)
        raise RuntimeError(f"YouTube 인증 오류: 유효하지 않거나 만료된 새로고침 토큰. {e}")

    try:
        # YouTube Data API 서비스 객체 생성 (버전 v3)
        youtube = build('youtube', 'v3', credentials=creds)
        logger.info("✅ YouTube Data API 서비스 객체 생성 완료.")
        return youtube
    except Exception as e:
        logger.error(f"❌ YouTube API 서비스 빌드 실패: {e}", exc_info=True)
        raise RuntimeError(f"YouTube 서비스 빌드 오류: {e}")

def upload_video_to_youtube(client_id, client_secret, refresh_token,
                            file_path, title, description, tags=None, category_id="28", privacy_status="private"):
    """
    주어진 비디오 파일을 YouTube에 업로드합니다.

    Args:
        client_id (str): Google Cloud Project의 OAuth 2.0 클라이언트 ID.
        client_secret (str): Google Cloud Project의 OAuth 2.0 클라이언트 시크릿.
        refresh_token (str): YouTube 계정의 새로고침 토큰.
        file_path (str): 업로드할 비디오 파일의 로컬 경로.
        title (str): 비디오 제목.
        description (str): 비디오 설명.
        tags (list, optional): 비디오 태그 목록. Defaults to None.
        category_id (str, optional): YouTube 비디오 카테고리 ID (예: 28 for Science & Technology).
                                     유튜브 API 문서 참조 (https://developers.google.com/youtube/v3/docs/videoCategories/list)
        privacy_status (str, optional): 비디오의 공개 상태 ('public', 'private', 'unlisted'). Defaults to 'private'.

    Returns:
        dict: 업로드된 비디오 정보 (성공 시), 또는 None (실패 시).
    """
    if not os.path.exists(file_path):
        logger.error(f"❌ 비디오 파일이 존재하지 않습니다: {file_path}")
        raise FileNotFoundError(f"업로드할 비디오 파일이 없습니다: {file_path}")

    try:
        youtube = get_authenticated_service(client_id, client_secret, refresh_token)
    except RuntimeError as e:
        logger.error(f"YouTube 서비스 인증 실패: {e}")
        return None

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags if tags else [],
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False # 아동용 콘텐츠 여부 (필수 설정)
        },
        'kind': 'youtube#video'
    }

    # 미디어 파일 업로드 준비
    media_body = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    logger.info(f"📤 YouTube에 비디오 업로드 시작: '{title}' (파일: {file_path})")
    try:
        # 실제 업로드 요청
        insert_request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media_body
        )
        response = None
        # resumable=True를 사용했으므로 진행 상태를 모니터링할 수 있습니다.
        while response is None:
            status, response = insert_request.next_chunk()
            if status:
                logger.info(f"업로드 진행률: {int(status.progress() * 100)}%")

        logger.info(f"✅ YouTube 비디오 업로드 성공! 비디오 ID: {response.get('id')}")
        return response

    except HttpError as e:
        logger.error(f"❌ YouTube API 업로드 오류: {e.resp.status} - {e.content.decode()}", exc_info=True)
        # 구체적인 오류 응답을 파싱하여 더 자세한 정보 제공
        try:
            error_details = json.loads(e.content.decode())
            logger.error(f"YouTube API 에러 상세: {json.dumps(error_details, indent=2)}")
        except json.JSONDecodeError:
            pass # JSON 디코딩 실패 시 무시
        raise RuntimeError(f"YouTube 업로드 실패: {e}")
    except Exception as e:
        logger.error(f"❌ 예기치 않은 YouTube 업로드 오류: {e}", exc_info=True)
        raise RuntimeError(f"YouTube 업로드 실패 (예기치 않은 오류): {e}")


if __name__ == '__main__':
    # 로컬 테스트를 위한 더미 환경 변수 및 파일 생성 (실제 사용 시 환경 변수 설정 필요)
    # 이 부분은 실제 API 키 대신 더미 값을 사용하므로, 실제 업로드는 불가능합니다.
    # .env 파일 또는 환경 변수로 실제 값을 설정해야 합니다.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("YouTube Uploader 모듈 로컬 테스트를 시작합니다.")
    print("경고: 실제 업로드를 위해서는 유효한 YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN 환경 변수가 필요합니다.")

    # 더미 환경 변수 설정 (로컬 테스트용)
    os.environ['YOUTUBE_CLIENT_ID'] = os.getenv('YOUTUBE_CLIENT_ID', 'YOUR_YOUTUBE_CLIENT_ID')
    os.environ['YOUTUBE_CLIENT_SECRET'] = os.getenv('YOUTUBE_CLIENT_SECRET', 'YOUR_YOUTUBE_CLIENT_SECRET')
    os.environ['YOUTUBE_REFRESH_TOKEN'] = os.getenv('YOUTUBE_REFRESH_TOKEN', 'YOUR_YOUTUBE_REFRESH_TOKEN')

    # 더미 비디오 파일 생성 (테스트용)
    dummy_video_path = "dummy_video.mp4"
    if not os.path.exists(dummy_video_path):
        with open(dummy_video_path, 'w') as f:
            f.write("This is a dummy video file for testing purposes.")
        print(f"더미 비디오 파일 생성됨: {dummy_video_path}")

    try:
        # 업로드 함수 호출 (실제 환경 변수 필요)
        response = upload_video_to_youtube(
            os.environ['YOUTUBE_CLIENT_ID'],
            os.environ['YOUTUBE_CLIENT_SECRET'],
            os.environ['YOUTUBE_REFRESH_TOKEN'],
            dummy_video_path,
            "테스트 비디오 제목 - 자동 업로드",
            "이것은 파이썬 스크립트에 의해 자동 업로드된 테스트 비디오입니다.",
            tags=["테스트", "자동화", "API"]
        )
        if response:
            print(f"업로드된 비디오 ID: {response.get('id')}")
        else:
            print("비디오 업로드 실패 (자세한 내용은 로그 확인)")
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
    finally:
        # 더미 파일 정리
        if os.path.exists(dummy_video_path):
            os.remove(dummy_video_path)
            print(f"더미 비디오 파일 삭제됨: {dummy_video_path}")
