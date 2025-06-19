import os
import random
import logging
from datetime import datetime, timedelta
import google.generativeai as genai
from openai import OpenAI
from src.config import Config

logger = logging.getLogger(__name__)

class AIRotationManager:
    def __init__(self):
        self.gemini_keys = Config.get_gemini_keys()
        self.openai_keys = Config.get_openai_keys()
        self.gemini_idx = 0
        self.openai_idx = 0
        self.model_usage = {'gemini': 0, 'openai': 0} # 일일 사용량
        self.last_reset_date = datetime.now().date()

    def _reset_daily_usage(self):
        if datetime.now().date() != self.last_reset_date:
            self.model_usage = {'gemini': 0, 'openai': 0}
            self.last_reset_date = datetime.now().date()
            logger.info("Daily API usage reset.")

    def get_next_gemini_model(self):
        self._reset_daily_usage()
        if not self.gemini_keys:
            raise ValueError("No Gemini API keys configured.")
        
        # 단일 키일 경우
        if len(self.gemini_keys) == 1:
            genai.configure(api_key=self.gemini_keys[0])
            logger.info(f"Using single Gemini API key.")
            return "gemini-pro"
            
        # 여러 키일 경우 라운드 로빈 로테이션 (현재는 단일 키 가정)
        # 실제 로테이션이 필요한 경우 아래 로직을 확장
        api_key = self.gemini_keys[self.gemini_idx]
        genai.configure(api_key=api_key)
        self.gemini_idx = (self.gemini_idx + 1) % len(self.gemini_keys)
        logger.info(f"Using Gemini API key ending with {api_key[-5:]} for next request.")
        self.model_usage['gemini'] += 1
        return "gemini-pro" # 또는 "gemini-1.5-flash", "gemini-1.5-pro" 등 필요에 따라 변경

    def get_next_openai_client(self):
        self._reset_daily_usage()
        if not self.openai_keys:
            raise ValueError("No OpenAI API keys configured.")
        
        api_key = self.openai_keys[self.openai_idx]
        client = OpenAI(api_key=api_key)
        self.openai_idx = (self.openai_idx + 1) % len(self.openai_keys)
        logger.info(f"Using OpenAI API key ending with {api_key[-5:]} for next request.")
        self.model_usage['openai'] += 1
        return client

    def get_llm_model(self, prefer_model: str = "gemini"):
        # 하루 5개 영상 생성을 가정, 각 AI의 사용량을 추적하여 쿼터 관리
        # 더 복잡한 쿼터 관리는 각 API의 상세 쿼터 정책에 따라 조정 필요
        if prefer_model == "gemini" and self.model_usage['gemini'] < 3 and self.gemini_keys: # 예시: 하루 Gemini 최대 3회 사용
            logger.info("Selecting Gemini model.")
            return "gemini"
        elif prefer_model == "openai" and self.model_usage['openai'] < 3 and self.openai_keys: # 예시: 하루 OpenAI 최대 3회 사용
            logger.info("Selecting OpenAI model.")
            return "openai"
        elif self.gemini_keys and self.model_usage['gemini'] < 3:
            logger.info("Fallback to Gemini model.")
            return "gemini"
        elif self.openai_keys and self.model_usage['openai'] < 3:
            logger.info("Fallback to OpenAI model.")
            return "openai"
        else:
            logger.warning("Both Gemini and OpenAI daily quotas might be reached or keys are missing. Attempting random selection.")
            if self.gemini_keys and self.openai_keys:
                return random.choice(["gemini", "openai"])
            elif self.gemini_keys:
                return "gemini"
            elif self.openai_keys:
                return "openai"
            else:
                raise ValueError("No valid AI models available or all quotas exceeded.")

    def get_current_model_usage(self):
        self._reset_daily_usage()
        return self.model_usage

# 전역 인스턴스 (필요시 Singleton 패턴 적용 가능)
ai_manager = AIRotationManager()
