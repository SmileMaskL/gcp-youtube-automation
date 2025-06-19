import os
import json
import logging

logger = logging.getLogger(__name__)

class AIRotation:
    def __init__(self):
        try:
            self.keys = json.loads(os.getenv('OPENAI_API_KEYS'))
            self.index = 0
            logger.info(f"✅ API 키 로테이션 초기화 (총 {len(self.keys)}개 키)")
        except Exception as e:
            logger.error(f"❌ API 키 로테이션 초기화 실패: {e}")
            raise

    def get_next_key(self):
        """다음 API 키 반환 (순환 방식)"""
        key = self.keys[self.index]
        self.index = (self.index + 1) % len(self.keys)
        logger.info(f"🔑 사용된 API 키 인덱스: {self.index}/{len(self.keys)}")
        return key
