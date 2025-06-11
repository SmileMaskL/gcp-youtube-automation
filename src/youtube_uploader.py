import os
import json
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

logger = logging.getLogger(__name__)

class YouTubeUploader:
    def __init__(self, client_secrets_data):
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        self.API_SERVICE_NAME = 'youtube'
        self.API_VERSION = 'v3'
        self.client_secrets_data = client_secrets_data
        self.youtube = None
        
    def authenticate(self):
        """YouTube API 인증"""
        try:
            credentials = None
            
            # 저장된 토큰이 있는지 확인
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    credentials = pickle.load(token)
            
            # 유효한 자격 증명이 없는 경우
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                else:
                    # client_secrets.json 파일을 임시로 생성
                    with open('client_secrets.json', 'w') as f:
                        json.dump(self.client_secrets_data, f)
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'client_secrets.json', self.SCOPES)
                    credentials = flow.run_local_server(port=0)
                    
                    # 임시 파일 삭제
                    os.remove('client_secrets.json')
                
                # 토큰 저장
                with open('token.pickle', 'wb') as token:
                    pickle.dump(credentials, token)
            
            # YouTube API 클라이언트 생성
            self.youtube = build(self.API_SERVICE_NAME, self.API_VERSION, credentials=credentials)
            logger.info("YouTube API 인증 성공")
            
        except Exception as e:
            logger.error(f"YouTube API 인증 실패: {str(e)}")
            raise
    
    def upload_video(self, video_path, thumbnail_path, title, description, tags=None, privacy_status='public'):
        """비디오 업로드"""
        try:
            if not self.youtube:
                self.authenticate()
            
            # 기본 태그 설정
            if tags is None:
                tags = ['shorts', '쇼츠', 'youtube', '유튜브', 'ai', '인공지능']
            
            # 비디오 메타데이터
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': '22',  # People & Blogs
                    'defaultLanguage': 'ko',
                    'defaultAudioLanguage': 'ko'
                },
                'status': {
                    'privacyStatus': privacy_status,  # 'private', 'public', 'unlisted'
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # 비디오 파일 업로드
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/mp4'
            )
            
            # 업로드 요청
            insert_request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            # 업로드 실행
            video_response = self._resumable_upload(insert_request)
            
            if video_response:
                video_id = video_response['id']
                logger.info(f"비디오 업로드 성공: {video_id}")
                
                # 썸네일 업로드
                if thumbnail_path and os.path.exists(thumbnail_path):
                    self.upload_thumbnail(video_id, thumbnail_path)
                
                return video_id
            else:
                raise Exception("비디오 업로드 실패")
                
        except HttpError as e:
            logger.error(f"YouTube API 오류: {e}")
            raise
        except Exception as e:
            logger.error(f"비디오 업로드 실패: {str(e)}")
            raise
    
    def upload_thumbnail(self, video_id, thumbnail_path):
        """썸네일 업로드"""
        try:
            if not os.path.exists(thumbnail_path):
                logger.warning(f"썸네일 파일이 존재하지 않음: {thumbnail_path}")
                return
            
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
            ).execute()
            
            logger.info(f"썸네일 업로드 성공: {video_id}")
            
        except HttpError as e:
            logger.error(f"썸네일 업로드 오류: {e}")
        except Exception as e:
            logger.error(f"썸네일 업로드 실패: {str(e)}")
    
    def _resumable_upload(self, insert_request):
        """재개 가능한 업로드"""
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        logger.info(f"업로드 완료. 비디오 ID: {response['id']}")
                        return response
                    else:
                        raise Exception(f"업로드 실패: {response}")
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    error = f"재시도 가능한 HTTP 에러 {e.resp.status}: {e}"
                    logger.warning(error)
                else:
                    raise e
            except Exception as e:
                error = f"재시도 가능한 에러: {e}"
                logger.warning(error)
            
            if error is not None:
                retry += 1
                if retry > 3:
                    raise Exception("최대 재시도 횟수 초과")
                
                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                logger.info(f"{sleep_seconds:.2f}초 후 재시도...")
                time.sleep(sleep_seconds)
        
        return response
    
    def get_video_info(self, video_id):
        """비디오 정보 조회"""
        try:
            if not self.youtube:
                self.authenticate()
            
            response = self.youtube.videos().list(
                part='snippet,statistics,status',
                id=video_id
            ).execute()
            
            if response['items']:
                return response['items'][0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"비디오 정보 조회 실패: {str(e)}")
            return None
    
    def update_video(self, video_id, title=None, description=None, tags=None):
        """비디오 정보 업데이트"""
        try:
            if not self.youtube:
                self.authenticate()
            
            # 현재 비디오 정보 가져오기
            current_video = self.get_video_info(video_id)
            if not current_video:
                raise Exception("비디오를 찾을 수 없음")
            
            # 업데이트할 정보 설정
            snippet = current_video['snippet']
            
            if title:
                snippet['title'] = title
            if description:
                snippet['description'] = description
            if tags:
                snippet['tags'] = tags
            
            # 업데이트 요청
            update_response = self.youtube.videos().update(
                part='snippet',
                body={
                    'id': video_id,
                    'snippet': snippet
                }
            ).execute()
            
            logger.info(f"비디오 정보 업데이트 성공: {video_id}")
            return update_response
            
        except Exception as e:
            logger.error(f"비디오 정보 업데이트 실패: {str(e)}")
            raise
    
    def delete_video(self, video_id):
        """비디오 삭제"""
        try:
            if not self.youtube:
                self.authenticate()
            
            self.youtube.videos().delete(id=video_id).execute()
            logger.info(f"비디오 삭제 성공: {video_id}")
            
        except Exception as e:
            logger.error(f"비디오 삭제 실패: {str(e)}")
            raise
    
    def get_channel_info(self):
        """채널 정보 조회"""
        try:
            if not self.youtube:
                self.authenticate()
            
            response = self.youtube.channels().list(
                part='snippet,statistics',
                mine=True
            ).execute()
            
            if response['items']:
                return response['items'][0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"채널 정보 조회 실패: {str(e)}")
            return None
