import os
import json
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class YouTubeUploader:
    def __init__(self, credentials_json=None):
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        self.API_SERVICE_NAME = 'youtube'
        self.API_VERSION = 'v3'
        self.youtube = None
        self.credentials_json = credentials_json
        
        if credentials_json:
            self.setup_credentials_from_json(credentials_json)
    
    def setup_credentials_from_json(self, credentials_json):
        """JSON 문자열에서 인증 정보 설정"""
        try:
            creds_data = json.loads(credentials_json)
            
            # OAuth2 인증 정보 생성
            creds = Credentials.from_authorized_user_info(creds_data, self.SCOPES)
            
            # 토큰이 만료되었으면 갱신
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            # YouTube API 클라이언트 생성
            self.youtube = build(self.API_SERVICE_NAME, self.API_VERSION, credentials=creds)
            logger.info("YouTube API 인증 완료")
            
        except Exception as e:
            logger.error(f"YouTube 인증 설정 실패: {e}")
            raise
    
    def setup_credentials_from_file(self, credentials_file='credentials.json', token_file='token.json'):
        """파일에서 인증 정보 설정"""
        try:
            creds = None
            
            # 기존 토큰 파일이 있으면 로드
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
            
            # 유효한 인증 정보가 없으면 OAuth 플로우 실행
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # 토큰 저장
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            # YouTube API 클라이언트 생성
            self.youtube = build(self.API_SERVICE_NAME, self.API_VERSION, credentials=creds)
            logger.info("YouTube API 인증 완료")
            
        except Exception as e:
            logger.error(f"YouTube 인증 설정 실패: {e}")
            raise
    
    def generate_tags(self, title, topic):
        """제목과 주제에서 태그 생성"""
        try:
            tags = []
            
            # 기본 태그
            base_tags = ['shorts', '짧은영상', '꿀팁', 'tip']
            tags.extend(base_tags)
            
            # 주제별 태그
            topic_lower = topic.lower()
            if '돈' in topic or 'money' in topic_lower:
                tags.extend(['돈벌기', '부업', '수익', '재테크', 'money', 'income'])
            elif '요리' in topic or 'cooking' in topic_lower:
                tags.extend(['요리', '레시피', 'cooking', 'recipe', '음식'])
            elif '운동' in topic or 'fitness' in topic_lower:
                tags.extend(['운동', '헬스', 'fitness', '다이어트', 'workout'])
            elif '공부' in topic or 'study' in topic_lower:
                tags.extend(['공부', '학습', 'study', '교육', 'education'])
            
            # 제목에서 키워드 추출
            title_words = title.replace('(', ' ').replace(')', ' ').split()
            for word in title_words:
                if len(word) > 1 and word not in tags:
                    tags.append(word)
            
            # 최대 15개로 제한
            return tags[:15]
            
        except Exception as e:
            logger.error(f"태그 생성 실패: {e}")
            return ['shorts', '꿀팁']
    
    def generate_description(self, title, topic):
        """설명 생성"""
        try:
            description = f"""🎯 {title}

📌 이 영상에서 다루는 내용:
• {topic}에 대한 핵심 정보
• 실제로 적용 가능한 팁
• 짧은 시간에 핵심만!

💡 더 많은 유용한 정보가 궁금하다면 구독과 좋아요 부탁드려요!

🔔 알림 설정까지 해두시면 새로운 꿀팁을 놓치지 않으실 수 있어요!

#Shorts #꿀팁 #{topic.replace(' ', '')}

⏰ 업로드 시간: {datetime.now().strftime('%Y년 %m월 %d일')}

📧 비즈니스 문의: business@example.com

⚠️ 면책조항: 이 영상의 내용은 정보 제공 목적이며, 개인의 상황에 따라 결과가 다를 수 있습니다."""

            return description
            
        except Exception as e:
            logger.error(f"설명 생성 실패: {e}")
            return f"{title}\n\n#Shorts #꿀팁"
    
    def upload_video(self, video_path, title, topic, thumbnail_path=None, privacy_status='public'):
        """비디오 업로드"""
        try:
            if not self.youtube:
                logger.error("YouTube API가 초기화되지 않았습니다")
                return None
            
            if not os.path.exists(video_path):
                logger.error(f"비디오 파일을 찾을 수 없습니다: {video_path}")
                return None
            
            logger.info(f"YouTube 업로드 시작: {title}")
            
            # 태그와 설명 생성
            tags = self.generate_tags(title, topic)
            description = self.generate_description(title, topic)
            
            # 업로드 메타데이터
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': '26',  # Howto & Style
                    'defaultLanguage': 'ko',
                    'defaultAudioLanguage': 'ko'
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # 비디오 파일 업로드
            media = MediaFileUpload(
                video_path,
                chunksize=1024*1024,  # 1MB chunks
                resumable=True,
                mimetype='video/mp4'
            )
            
            # 업로드 요청
            insert_request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            # 재시도 로직이 포함된 업로드 실행
            video_id = self.resumable_upload(insert_request)
            
            if video_id:
                logger.info(f"업로드 완료! Video ID: {video_id}")
                
                # 썸네일 업로드
                if thumbnail_path and os.path.exists(thumbnail_path):
                    self.upload_thumbnail(video_id, thumbnail_path)
                
                return {
                    'video_id': video_id,
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'title': title,
                    'upload_time': datetime.now().isoformat()
                }
            else:
                logger.error("비디오 업로드 실패")
                return None
                
        except HttpError as e:
            logger.error(f"YouTube API 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"업로드 실패: {e}")
            return None
    
    def resumable_upload(self, insert_request):
        """재시도 가능한 업로드"""
        response = None
        error = None
        retry = 0
        max_retries = 3
        
        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        return response['id']
                    else:
                        logger.error(f"업로드 실패: {response}")
                        return None
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    # 서버 오류 - 재시도
                    error = f"서버 오류 (HTTP {e.resp.status}): {e}"
                    retry += 1
                    if retry > max_retries:
                        logger.error(f"최대 재시도 횟수 초과: {error}")
                        return None
                    
                    wait_time = 2 ** retry
                    logger.warning(f"재시도 대기 중... ({wait_time}초)")
                    time.sleep(wait_time)
                else:
                    # 클라이언트 오류 - 재시도하지 않음
                    logger.error(f"클라이언트 오류: {e}")
                    return None
            except Exception as e:
                logger.error(f"예상치 못한 오류: {e}")
                return None
        
        return None
    
    def upload_thumbnail(self, video_id, thumbnail_path):
        """썸네일 업로드"""
        try:
            if not os.path.exists(thumbnail_path):
                logger.warning(f"썸네일 파일을 찾을 수 없습니다: {thumbnail_path}")
                return False
            
            logger.info(f"썸네일 업로드 중: {video_id}")
            
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
            ).execute()
            
            logger.info("썸네일 업로드 완료")
            return True
            
        except HttpError as e:
            logger.error(f"썸네일 업로드 실패: {e}")
            return False
        except Exception as e:
            logger.error(f"썸네일 업로드 오류: {e}")
            return False
    
    def get_channel_info(self):
        """채널 정보 조회"""
        try:
            if not self.youtube:
                return None
            
            response = self.youtube.channels().list(
                part='snippet,statistics',
                mine=True
            ).execute()
            
            if 'items' in response and len(response['items']) > 0:
                channel = response['items'][0]
                return {
                    'channel_id': channel['id'],
                    'title': channel['snippet']['title'],
                    'description': channel['snippet']['description'],
                    'subscriber_count': channel['statistics'].get('subscriberCount', 0),
                    'video_count': channel['statistics'].get('videoCount', 0),
                    'view_count': channel['statistics'].get('viewCount', 0)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"채널 정보 조회 실패: {e}")
            return None
    
    def get_video_status(self, video_id):
        """비디오 상태 확인"""
        try:
            if not self.youtube:
                return None
            
            response = self.youtube.videos().list(
                part='status,processingDetails',
                id=video_id
            ).execute()
            
            if 'items' in response and len(response['items']) > 0:
                video = response['items'][0]
                return {
                    'upload_status': video['status'].get('uploadStatus'),
                    'privacy_status': video['status'].get('privacyStatus'),
                    'processing_status': video.get('processingDetails', {}).get('processingStatus'),
                    'processing_progress': video.get('processingDetails', {}).get('processingProgress')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"비디오 상태 확인 실패: {e}")
            return None

if __name__ == "__main__":
    # 테스트
    uploader = YouTubeUploader()
    
    # 채널 정보 테스트
    channel_info = uploader.get_channel_info()
    if channel_info:
        print(f"채널 정보: {channel_info}")
    else:
        print("채널 정보 조회 실패")
