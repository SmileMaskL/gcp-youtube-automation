import os
import requests
import json
import logging
from datetime import datetime
import openai
import google.generativeai as genai
from elevenlabs import generate, save
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip
from src.video_creator import VideoCreator
from src.thumbnail_generator import ThumbnailGenerator
import traceback

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self, pexels_api_key, openai_api_key, gemini_api_key, elevenlabs_api_key, elevenlabs_voice_id):
        self.pexels_api_key = pexels_api_key
        self.openai_api_key = openai_api_key
        self.gemini_api_key = gemini_api_key
        self.elevenlabs_api_key = elevenlabs_api_key
        self.elevenlabs_voice_id = elevenlabs_voice_id
        
        # API 클라이언트 설정
        openai.api_key = self.openai_api_key
        genai.configure(api_key=self.gemini_api_key)
        
        # 모델 설정
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        # 비디오 및 썸네일 생성기
        self.video_creator = VideoCreator()
        self.thumbnail_generator = ThumbnailGenerator()
        
    def generate_script(self, topic):
        """AI를 사용해 대본 생성 (Gemini 사용)"""
        try:
            prompt = f"""
            주제: {topic}
            
            YouTube Shorts용 60초 분량의 매력적인 대본을 작성해주세요.
            
            요구사항:
            1. 첫 3초 안에 시청자의 관심을 끌어야 함
            2. 실용적이고 가치 있는 정보 제공
            3. 수익 창출과 관련된 구체적인 팁 포함
            4. 친근하고 에너지 넘치는 톤
            5. 마지막에 구독과 좋아요 유도
            6. 총 150-200단어 내외
            
            대본 형식:
            [훅] (첫 3초)
            [메인 내용] (40초)
            [마무리/CTA] (15초)
            """
            
            response = self.gemini_model.generate_content(prompt)
            script = response.text
            
            logger.info("✅ AI 대본 생성 완료")
            return script
            
        except Exception as e:
            logger.error(f"❌ 대본 생성 실패: {str(e)}")
            # 백업 대본
            return f"""
            [훅] {topic}로 돈 버는 방법, 3초만 투자하세요!
            
            [메인 내용] 
            첫 번째, 기초부터 탄탄히 공부하세요. 무료 강의와 책을 활용하면 충분합니다.
            두 번째, 실전 경험을 쌓으세요. 작은 프로젝트부터 시작해서 포트폴리오를 만드세요.
            세 번째, 네트워킹이 핵심입니다. 온라인 커뮤니티에서 활발히 활동하세요.
            네 번째, 꾸준함이 성공의 열쇠입니다. 매일 조금씩이라도 계속 발전시키세요.
            
            [마무리] 
            이 방법들을 실천하면 분명 성과를 볼 수 있을 거예요. 
            더 많은 수익 팁이 궁금하다면 구독과 좋아요 눌러주세요!
            """
    
    def generate_tts_audio(self, script):
        """텍스트를 음성으로 변환 (ElevenLabs)"""
        try:
            # 대본에서 특수 문자 제거
            clean_script = script.replace('[훅]', '').replace('[메인 내용]', '').replace('[마무리/CTA]', '').replace('[마무리]', '')
            clean_script = clean_script.strip()
            
            audio = generate(
                text=clean_script,
                voice=self.elevenlabs_voice_id,
                api_key=self.elevenlabs_api_key,
                model="eleven_multilingual_v2"
            )
            
            # 임시 파일로 저장
            audio_path = f"/tmp/audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            save(audio, audio_path)
            
            logger.info("✅ TTS 음성 생성 완료")
            return audio_path
            
        except Exception as e:
            logger.error(f"❌ TTS 생성 실패: {str(e)}")
            return None
    
    def search_pexels_videos(self, query, per_page=10):
        """Pexels에서 비디오 검색"""
        try:
            url = "https://api.pexels.com/videos/search"
            headers = {"Authorization": self.pexels_api_key}
            params = {
                "query": query,
                "per_page": per_page,
                "orientation": "portrait",  # 세로 영상
                "size": "medium"
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = data.get('videos', [])
            
            logger.info(f"✅ Pexels 비디오 검색 완료: {len(videos)}개")
            return videos
            
        except Exception as e:
            logger.error(f"❌ Pexels 비디오 검색 실패: {str(e)}")
            return []
    
    def download_video(self, video_url, filename):
        """비디오 다운로드"""
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ 비디오 다운로드 완료: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ 비디오 다운로드 실패: {str(e)}")
            return None
    
    def generate_video_content(self, topic):
        """전체 비디오 컨텐츠 생성 프로세스"""
        try:
            logger.info(f"🎬 비디오 컨텐츠 생성 시작: {topic}")
            
            # 1. AI 대본 생성
            script = self.generate_script(topic)
            logger.info("1/6 대본 생성 완료")
            
            # 2. TTS 음성 생성
            audio_path = self.generate_tts_audio(script)
            if not audio_path:
                logger.error("❌ 음성 생성 실패")
                return None
            logger.info("2/6 음성 생성 완료")
            
            # 3. 관련 비디오 검색 및 다운로드
            search_terms = [
                "business success", "money making", "entrepreneur", 
                "investment", "technology", "programming", "startup"
            ]
            
            videos = []
            for term in search_terms[:3]:  # 최대 3개 검색어
                pexels_videos = self.search_pexels_videos(term, 5)
                videos.extend(pexels_videos[:2])  # 각 검색어당 2개씩
            
            if not videos:
                logger.error("❌ 적절한 비디오를 찾을 수 없음")
                return None
            
            # 비디오 다운로드
            video_files = []
            for i, video in enumerate(videos[:3]):  # 최대 3개 비디오
                video_url = video['video_files'][0]['link']
                filename = f"/tmp/video_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                downloaded_file = self.download_video(video_url, filename)
                if downloaded_file:
                    video_files.append(downloaded_file)
            
            logger.info("3/6 비디오 다운로드 완료")
            
            # 4. 비디오 편집 (음성 길이에 맞춰)
            final_video_path = self.video_creator.create_shorts_video(
                video_files=video_files,
                audio_path=audio_path,
                script=script,
                topic=topic
            )
            
            if not final_video_path:
                logger.error("❌ 비디오 편집 실패")
                return None
            
            logger.info("4/6 비디오 편집 완료")
            
            # 5. 썸네일 생성
            thumbnail_path = self.thumbnail_generator.create_thumbnail(
                topic=topic,
                script=script[:100] + "..."  # 첫 100자만 사용
            )
            
            logger.info("5/6 썸네일 생성 완료")
            
            # 6. 메타데이터 생성
            title = self.generate_title(topic)
            description = self.generate_description(topic, script)
            tags = self.generate_tags(topic)
            
            logger.info("6/6 메타데이터 생성 완료")
            
            # 결과 반환
            result = {
                'title': title,
                'description': description,
                'tags': tags,
                'script': script,
                'video_path': final_video_path,
                'thumbnail_path': thumbnail_path,
                'audio_path': audio_path,
                'topic': topic,
                'created_at': datetime.now().isoformat()
            }
            
            logger.info("✅ 전체 비디오 컨텐츠 생성 완료")
            return result
            
        except Exception as e:
            logger.error(f"❌ 비디오 컨텐츠 생성 중 오류: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def generate_title(self, topic):
        """매력적인 제목 생성"""
        titles = [
            f"{topic}로 월 100만원 벌기 (실제 후기)",
            f"이것만 알면 {topic} 마스터 #Shorts",
            f"{topic} 비밀 공개 (99%가 모름)",
            f"{topic}로 부자 되는 법 (3분 요약)",
            f"실제로 {topic}으로 성공한 방법
