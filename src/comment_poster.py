"""
YouTube 댓글 자동 게시 모듈
"""
import logging
import time
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

from utils import config_manager, RateLimiter, retry_on_failure

logger = logging.getLogger(__name__)


class CommentPoster:
    """YouTube 댓글 자동 게시기"""

    def __init__(self, credentials_file: str = "credentials.json",
                 token_file: str = "token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.youtube = None
        self.rate_limiter = RateLimiter(
            max_calls=100, time_window=100)  # YouTube API 제한

        # 댓글 템플릿 로드
        self.comment_templates = self._load_comment_templates()

        # 설정 로드
        self.config = config_manager.get('comments', {
            'auto_post': False,
            'delay_min': 30,
            'delay_max': 180,
            'max_comments_per_video': 3,
            'enable_replies': True,
            'reply_probability': 0.3
        })

    def _load_comment_templates(self) -> Dict:
        """댓글 템플릿 로드"""
        template_file = Path("comment_templates.json")

        default_templates = {
            "positive": [
                "정말 유용한 정보네요! 감사합니다 👍",
                "좋은 영상 감사드려요! 구독하고 갑니다 🔔",
                "항상 좋은 컨텐츠 만들어주셔서 감사해요!",
                "이런 정보를 찾고 있었는데 딱 맞네요!",
                "설명이 정말 이해하기 쉬워요 ✨",
                "도움이 많이 됐습니다! 다음 영상도 기대할게요"
            ],
            "questions": [
                "혹시 이 부분에 대해서 더 자세히 설명해주실 수 있나요?",
                "이것과 관련된 다른 팁도 있을까요?",
                "초보자도 따라할 수 있을까요?",
                "이 방법 말고 다른 방식도 있나요?",
                "어느 정도 시간이 걸리는지 궁금해요"
            ],
            "engagement": [
                "다른 분들은 어떻게 생각하시나요?",
                "댓글로 경험 공유해주세요!",
                "좋아요 많이 눌러주세요! 👍",
                "구독자 여러분의 의견이 궁금해요",
                "이 방법 써보신 분 계신가요?"
            ],
            "replies": [
                "좋은 의견 감사합니다!",
                "맞아요! 저도 그렇게 생각해요",
                "도움이 되셨다니 기뻐요 😊",
                "좋은 질문이네요!",
                "감사합니다! 더 좋은 컨텐츠로 찾아뵐게요"
            ]
        }

        try:
            if template_file.exists():
                with open(template_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 기본 템플릿 저장
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(
                        default_templates,
                        f,
                        ensure_ascii=False,
                        indent=2)
                return default_templates
        except Exception as e:
            logger.error(f"댓글 템플릿 로드 실패: {e}")
            return default_templates

    def authenticate(self) -> bool:
        """YouTube API 인증"""
        try:
            creds = None

            # 기존 토큰 로드
            if Path(self.token_file).exists():
                creds = Credentials.from_authorized_user_file(self.token_file)

            # 토큰이 없거나 만료된 경우 새로 인증
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = Flow.from_client_secrets_file(
                        self.credentials_file,
                        scopes=['https://www.googleapis.com/auth/youtube.force-ssl'])
                    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

                    auth_url = flow.authorization_url(prompt='consent')[0]
                    print(f"다음 URL로 이동하여 인증하세요: {auth_url}")
                    code = input("인증 코드를 입력하세요: ")

                    flow.fetch_token(code=code)
                    creds = flow.credentials

                # 토큰 저장
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())

            # YouTube API 클라이언트 생성
            self.youtube = build('youtube', 'v3', credentials=creds)
            logger.info("YouTube API 인증 완료")
            return True

        except Exception as e:
            logger.error(f"YouTube API 인증 실패: {e}")
            return False

    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """비디오 정보 조회"""
        if not self.youtube:
            return None

        try:
            request = self.youtube.videos().list(
                part="snippet,statistics",
                id=video_id
            )
            response = request.execute()

            if response['items']:
                return response['items'][0]
            return None

        except HttpError as e:
            logger.error(f"비디오 정보 조회 실패: {e}")
            return None

    def get_video_comments(
            self,
            video_id: str,
            max_results: int = 50) -> List[Dict]:
        """비디오 댓글 조회"""
        if not self.youtube:
            return []

        try:
            comments = []
            request = self.youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=max_results,
                order="relevance"
            )

            while request and len(comments) < max_results:
                response = request.execute()

                for item in response['items']:
                    comment = {
                        'id': item['id'],
                        'text': item['snippet']['topLevelComment']['snippet']['textDisplay'],
                        'author': item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                        'likes': item['snippet']['topLevelComment']['snippet']['likeCount'],
                        'published': item['snippet']['topLevelComment']['snippet']['publishedAt'],
                        'replies': []}

                    # 답글 정보 추가
                    if 'replies' in item:
                        for reply in item['replies']['comments']:
                            comment['replies'].append({
                                'text': reply['snippet']['textDisplay'],
                                'author': reply['snippet']['authorDisplayName'],
                                'published': reply['snippet']['publishedAt']
                            })

                    comments.append(comment)

                request = self.youtube.commentThreads().list_next(request, response)

            return comments

        except HttpError as e:
            logger.error(f"댓글 조회 실패: {e}")
            return []

    @retry_on_failure(max_retries=3)
    def post_comment(self, video_id: str, text: str) -> Optional[str]:
        """댓글 게시"""
        if not self.youtube:
            return None

        try:
            # Rate limiting
            if not self.rate_limiter.can_make_call():
                wait_time = self.rate_limiter.wait_time()
                logger.info(f"API 제한으로 {wait_time:.1f}초 대기...")
                time.sleep(wait_time)

            self.rate_limiter.make_call()

            request = self.youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": text
                            }
                        }
                    }
                }
            )

            response = request.execute()
            comment_id = response['id']

            logger.info(f"댓글 게시 완료: {comment_id}")
            return comment_id

        except HttpError as e:
            if e.resp.status == 403:
                logger.error("댓글 게시 권한이 없습니다")
            elif e.resp.status == 400:
                logger.error("잘못된 요청입니다")
            else:
                logger.error(f"댓글 게시 실패: {e}")
            return None

    @retry_on_failure(max_retries=3)
    def reply_to_comment(self, comment_id: str, text: str) -> Optional[str]:
        """댓글에 답글 달기"""
        if not self.youtube:
            return None

        try:
            if not self.rate_limiter.can_make_call():
                wait_time = self.rate_limiter.wait_time()
                time.sleep(wait_time)

            self.rate_limiter.make_call()

            request = self.youtube.comments().insert(
                part="snippet",
                body={
                    "snippet": {
                        "parentId": comment_id,
                        "textOriginal": text
                    }
                }
            )

            response = request.execute()
            reply_id = response['id']

            logger.info(f"답글 게시 완료: {reply_id}")
            return reply_id

        except HttpError as e:
            logger.error(f"답글 게시 실패: {e}")
            return None

    def generate_contextual_comment(
            self,
            video_info: Dict,
            comment_type: str = "positive") -> str:
        """맥락에 맞는 댓글 생성"""
        templates = self.comment_templates.get(
            comment_type, self.comment_templates["positive"])

        # 기본 템플릿 선택
        base_comment = random.choice(templates)

        # 비디오 정보를 바탕으로 개인화
        title = video_info.get('snippet', {}).get('title', '')

        # 키워드 기반 댓글 커스터마이징
        keywords = {
            '튜토리얼': '따라하기 쉽게 설명해주셨네요!',
            '리뷰': '솔직한 리뷰 감사합니다!',
            '팁': '유용한 팁 감사해요!',
            '게임': '게임 실력이 대단하시네요!',
            '요리': '맛있어 보여요! 레시피 감사합니다',
            '여행': '가보고 싶은 곳이네요!',
            '음악': '좋은 음악 감사합니다! 🎵'
        }

        for keyword, custom_comment in keywords.items():
            if keyword in title:
                if random.random() < 0.3:  # 30% 확률로 커스텀 댓글 사용
                    base_comment = custom_comment
                break

        return base_comment

    def auto_comment_on_video(self, video_id: str) -> List[str]:
        """비디오에 자동 댓글 게시"""
        if not self.config['auto_post']:
            logger.info("자동 댓글 게시가 비활성화되어 있습니다")
            return []

        # 비디오 정보 조회
        video_info = self.get_video_info(video_id)
        if not video_info:
            logger.error("비디오 정보를 가져올 수 없습니다")
            return []

        posted_comments = []
        max_comments = self.config['max_comments_per_video']

        for i in range(max_comments):
            try:
                # 댓글 타입 랜덤 선택
                comment_types = ['positive', 'questions', 'engagement']
                comment_type = random.choice(comment_types)

                # 댓글 생성
                comment_text = self.generate_contextual_comment(
                    video_info, comment_type)

                # 댓글 게시
                comment_id = self.post_comment(video_id, comment_text)
                if comment_id:
                    posted_comments.append(comment_id)

                # 다음 댓글까지 대기
                if i < max_comments - 1:
                    delay = random.randint(
                        self.config['delay_min'], self.config['delay_max'])
                    logger.info(f"다음 댓글까지 {delay}초 대기...")
                    time.sleep(delay)

            except Exception as e:
                logger.error(f"댓글 게시 중 오류: {e}")

        return posted_comments

    def auto_reply_to_comments(self, video_id: str) -> List[str]:
        """댓글에 자동 답글"""
        if not self.config['enable_replies']:
            return []

        # 기존 댓글 조회
        comments = self.get_video_comments(video_id)
        replies_posted = []

        for comment in comments:
            # 확률적으로 답글 결정
            if random.random() > self.config['reply_probability']:
                continue

            # 이미 답글이 많은 댓글은 스킵
            if len(comment['replies']) > 5:
                continue

            try:
                reply_text = random.choice(self.comment_templates['replies'])
                reply_id = self.reply_to_comment(comment['id'], reply_text)

                if reply_id:
                    replies_posted.append(reply_id)

                # 답글 사이 대기
                time.sleep(random.randint(30, 120))

            except Exception as e:
                logger.error(f"답글 게시 중 오류: {e}")

        return replies_posted

    def schedule_comments(self, video_ids: List[str], schedule_time: datetime):
        """댓글 예약 게시"""
        logger.info(f"{len(video_ids)}개 비디오에 댓글 예약: {schedule_time}")

        while datetime.now() < schedule_time:
            time.sleep(60)  # 1분마다 체크

        logger.info("예약된 댓글 게시 시작")

        for video_id in video_ids:
            try:
                comments = self.auto_comment_on_video(video_id)
                logger.info(f"비디오 {video_id}에 {len(comments)}개 댓글 게시")

                # 비디오 사이 대기
                time.sleep(random.randint(300, 600))  # 5-10분 대기

            except Exception as e:
                logger.error(f"비디오 {video_id} 댓글 게시 실패: {e}")

    def get_comment_stats(self) -> Dict:
        """댓글 통계 조회"""
        # 실제 구현에서는 데이터베이스나 로그 파일에서 통계를 조회해야 함
        return {
            'total_comments': 0,
            'total_replies': 0,
            'success_rate': 0.0,
            'last_activity': datetime.now().isoformat()
        }


def main():
    """테스트 실행"""
    import sys

    if len(sys.argv) < 2:
        print("사용법: python comment_poster.py <video_id>")
        return

    video_id = sys.argv[1]
    poster = CommentPoster()

    if not poster.authenticate():
        print("인증 실패")
        return

    try:
        # 비디오 정보 조회
        video_info = poster.get_video_info(video_id)
        if video_info:
            title = video_info['snippet']['title']
            print(f"비디오: {title}")

            # 댓글 게시 테스트
            comments = poster.auto_comment_on_video(video_id)
            print(f"게시된 댓글: {len(comments)}개")

        else:
            print("비디오를 찾을 수 없습니다")

    except Exception as e:
        logger.error(f"실행 실패: {e}")


if __name__ == "__main__":
    main()
