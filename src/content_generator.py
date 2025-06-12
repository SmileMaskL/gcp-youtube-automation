import os
import json
import logging
import time
import random
from datetime import datetime
from typing import Dict, Optional, List
import requests
from google.cloud import storage
from google.api_core.exceptions import GoogleAPICallError
import openai
from google.generativeai import configure as configure_gemini
import google.generativeai as genai
from elevenlabs import generate, play, set_api_key, voices
from PIL import Image, ImageDraw, ImageFont
import moviepy.editor as mpe
from moviepy.video.tools.drawing import color_gradient
import numpy as np

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self, openai_api_key: str, gemini_api_key: str, elevenlabs_api_key: str, storage_bucket: str):
        """초기화"""
        self.openai_api_key = openai_api_key
        self.gemini_api_key = gemini_api_key
        self.elevenlabs_api_key = elevenlabs_api_key
        self.storage_bucket = storage_bucket
        self.gcs_client = storage.Client() if storage_bucket else None
        
        # API 설정
        openai.api_key = openai_api_key
        if gemini_api_key:
            configure_gemini(api_key=gemini_api_key)
        if elevenlabs_api_key:
            set_api_key(elevenlabs_api_key)
        
        # 초기화 확인
        logger.info("ContentGenerator 초기화 완료")
    
    def generate_script(self, topic: str, style: str = "informative", duration: int = 60) -> Optional[Dict]:
        """스크립트 생성"""
        try:
            logger.info(f"스크립트 생성 시작: {topic}")
            
            # 프롬프트 생성
            prompt = self._create_script_prompt(topic, style, duration)
            
            # 모델 선택 (Gemini가 있으면 사용, 없으면 OpenAI)
            if self.gemini_api_key:
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                script = response.text
            else:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful YouTube script writer."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                script = response.choices[0].message.content
            
            # 스크립트 파싱
            parsed_script = self._parse_script(script)
            
            if not parsed_script:
                logger.error("스크립트 파싱 실패")
                return None
            
            logger.info("스크립트 생성 완료")
            return parsed_script
            
        except Exception as e:
            logger.error(f"스크립트 생성 오류: {e}")
            return None
    
    def _create_script_prompt(self, topic: str, style: str, duration: int) -> str:
        """스크립트 생성을 위한 프롬프트 생성"""
        styles = {
            "informative": "정보 전달 위주로 전문적이면서도 이해하기 쉽게",
            "funny": "유머러스하고 재미있는 방식으로",
            "dramatic": "극적이고 감동적인 스토리텔링으로",
            "casual": "편안하고 대화체로"
        }
        
        selected_style = styles.get(style, styles["informative"])
        
        return f"""다음 요구사항에 맞는 유튜브 동영상 스크립트를 작성해주세요.

주제: {topic}
스타일: {selected_style}
길이: 약 {duration}초 분량 (약 {int(duration/60)}분)

스크립트 형식:
[제목]: 동영상 제목
[소개]: 2-3문장으로 간단한 소개
[본문]: 
- 주요 내용을 3-5개의 섹션으로 나누어 작성
- 각 섹션은 2-3문장으로 구성
- 자연스러운 말투로 작성
[마무리]: 시청자에게 질문이나 액션 유도 (좋아요, 구독 등)

실제로 {topic}으로 성공한 방법을 알려드리겠습니다. 시작해볼까요?"""
    
    def _parse_script(self, script_text: str) -> Dict:
        """생성된 스크립트 파싱"""
        try:
            result = {
                "title": "",
                "introduction": "",
                "sections": [],
                "conclusion": ""
            }
            
            lines = script_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith("[제목]:"):
                    result["title"] = line.replace("[제목]:", "").strip()
                elif line.startswith("[소개]:"):
                    result["introduction"] = line.replace("[소개]:", "").strip()
                elif line.startswith("- "):
                    if current_section:
                        current_section["content"].append(line[2:].strip())
                elif line.endswith(":"):
                    if current_section:
                        result["sections"].append(current_section)
                    current_section = {
                        "title": line[:-1].strip(),
                        "content": []
                    }
                elif line.startswith("[마무리]:"):
                    result["conclusion"] = line.replace("[마무리]:", "").strip()
            
            if current_section:
                result["sections"].append(current_section)
            
            return result
            
        except Exception as e:
            logger.error(f"스크립트 파싱 오류: {e}")
            return None
    
    def generate_audio(self, text: str, output_filename: str = "audio.mp3") -> Optional[str]:
        """오디오 생성"""
        try:
            logger.info("오디오 생성 시작")
            
            if not self.elevenlabs_api_key:
                logger.warning("ElevenLabs API 키가 없습니다. 오디오 생성 건너뜁니다.")
                return None
            
            # ElevenLabs에서 오디오 생성
            audio = generate(
                text=text,
                voice="Rachel",  # 기본 음성 설정
                model="eleven_monolingual_v2"
            )
            
            # 로컬에 저장
            local_path = f"/tmp/{output_filename}"
            with open(local_path, "wb") as f:
                f.write(audio)
            
            # GCS에 업로드
            gcs_path = self._upload_to_gcs(local_path, output_filename)
            
            logger.info(f"오디오 생성 완료: {gcs_path}")
            return gcs_path
            
        except Exception as e:
            logger.error(f"오디오 생성 오류: {e}")
            return None
    
    def generate_thumbnail(self, title: str, output_filename: str = "thumbnail.png") -> Optional[str]:
        """썸네일 생성"""
        try:
            logger.info("썸네일 생성 시작")
            
            # 이미지 생성 (간단한 버전)
            img = Image.new('RGB', (1280, 720), color=(73, 109, 137))
            d = ImageDraw.Draw(img)
            
            # 제목 텍스트 추가
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
            
            d.text((100, 300), title, fill=(255, 255, 255), font=font)
            
            # 로컬에 저장
            local_path = f"/tmp/{output_filename}"
            img.save(local_path)
            
            # GCS에 업로드
            gcs_path = self._upload_to_gcs(local_path, output_filename)
            
            logger.info(f"썸네일 생성 완료: {gcs_path}")
            return gcs_path
            
        except Exception as e:
            logger.error(f"썸네일 생성 오류: {e}")
            return None
    
    def generate_video(self, audio_path: str, thumbnail_path: str, output_filename: str = "video.mp4") -> Optional[str]:
        """비디오 생성"""
        try:
            logger.info("비디오 생성 시작")
            
            # 오디오 파일 로드
            audio_clip = mpe.AudioFileClip(audio_path)
            
            # 썸네일 이미지 로드 및 비디오 클립 생성
            image_clip = mpe.ImageClip(thumbnail_path, duration=audio_clip.duration)
            
            # 색상 그라데이션 배경 생성
            def make_frame(t):
                progress = t / audio_clip.duration
                r = int(50 + progress * 205)
                g = int(100 + progress * 155)
                b = int(150 + progress * 105)
                return np.array([[[r, g, b]] * (1280 * 720)], dtype=np.uint8).reshape(720, 1280, 3)
            
            color_clip = mpe.VideoClip(make_frame, duration=audio_clip.duration)
            
            # 최종 비디오 조합
            final_clip = mpe.CompositeVideoClip([
                color_clip,
                image_clip.set_position(('center', 'center'))
            ]).set_audio(audio_clip)
            
            # 로컬에 저장
            local_path = f"/tmp/{output_filename}"
            final_clip.write_videofile(local_path, fps=24, codec='libx264', audio_codec='aac')
            
            # GCS에 업로드
            gcs_path = self._upload_to_gcs(local_path, output_filename)
            
            logger.info(f"비디오 생성 완료: {gcs_path}")
            return gcs_path
            
        except Exception as e:
            logger.error(f"비디오 생성 오류: {e}")
            return None
    
    def _upload_to_gcs(self, local_path: str, destination_name: str) -> Optional[str]:
        """GCS에 파일 업로드"""
        if not self.storage_bucket or not self.gcs_client:
            logger.warning("GCS 버킷이 설정되지 않았습니다. 로컬 경로 반환")
            return local_path
            
        try:
            bucket = self.gcs_client.bucket(self.storage_bucket)
            blob = bucket.blob(destination_name)
            
            blob.upload_from_filename(local_path)
            
            # 공개 URL 생성
            blob.make_public()
            
            logger.info(f"GCS 업로드 완료: {blob.public_url}")
            return blob.public_url
            
        except GoogleAPICallError as e:
            logger.error(f"GCS 업로드 오류: {e}")
            return local_path
    
    def generate_complete_content(self, topic: str, style: str = "informative", duration: int = 60) -> Optional[Dict]:
        """완전한 컨텐츠 생성 (스크립트 + 오디오 + 썸네일 + 비디오)"""
        try:
            logger.info(f"전체 컨텐츠 생성 시작: {topic}")
            
            # 1. 스크립트 생성
            script = self.generate_script(topic, style, duration)
            if not script:
                logger.error("스크립트 생성 실패")
                return None
            
            full_text = f"{script['title']}\n\n{script['introduction']}\n\n"
            for section in script['sections']:
                full_text += f"{section['title']}\n"
                for content in section['content']:
                    full_text += f"- {content}\n"
                full_text += "\n"
            full_text += script['conclusion']
            
            # 2. 오디오 생성
            audio_path = self.generate_audio(full_text, "audio.mp3")
            if not audio_path:
                logger.error("오디오 생성 실패")
                return None
            
            # 3. 썸네일 생성
            thumbnail_path = self.generate_thumbnail(script['title'], "thumbnail.png")
            if not thumbnail_path:
                logger.error("썸네일 생성 실패")
                return None
            
            # 4. 비디오 생성
            video_path = self.generate_video(audio_path, thumbnail_path, "video.mp4")
            if not video_path:
                logger.error("비디오 생성 실패")
                return None
            
            logger.info("전체 컨텐츠 생성 완료")
            return {
                "title": script['title'],
                "script": script,
                "audio_path": audio_path,
                "thumbnail_path": thumbnail_path,
                "video_path": video_path
            }
            
        except Exception as e:
            logger.error(f"전체 컨텐츠 생성 오류: {e}")
            return None
