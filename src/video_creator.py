import os
import cv2
import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class VideoCreator:
    def __init__(self):
        self.output_width = 1080
        self.output_height = 1920  # 9:16 비율 (세로)
        self.font_path = os.path.join(os.path.dirname(__file__), '..', 'fonts', 'Catfont.ttf')
        
    def create_shorts_video(self, video_files, audio_path, script, topic):
        """YouTube Shorts용 세로 비디오 생성"""
        try:
            logger.info("🎬 YouTube Shorts 비디오 생성 시작")
            
            # 오디오 클립 로드하여 길이 확인
            audio_clip = AudioFileClip(audio_path)
            target_duration = audio_clip.duration
            
            logger.info(f"📏 목표 비디오 길이: {target_duration:.2f}초")
            
            # 비디오 클립들 처리
            video_clips = []
            total_video_duration = 0
            
            for video_file in video_files:
                try:
                    clip = VideoFileClip(video_file)
                    
                    # 세로 비율로 크롭 (9:16)
                    clip_resized = self.crop_to_vertical(clip)
                    
                    # 비디오 속도 조정 (더 다이나믹하게)
                    speed_factor = random.uniform(0.8, 1.2)
                    clip_speed = clip_resized.fx(speedx, speed_factor)
                    
                    video_clips.append(clip_speed)
                    total_video_duration += clip_speed.duration
                    
                    if total_video_duration >= target_duration * 1.5:  # 충분한 소스 확보
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ 비디오 파일 처리 실패: {video_file}, {str(e)}")
                    continue
            
            if not video_clips:
                logger.error("❌ 사용 가능한 비디오 클립이 없습니다")
                return None
            
            # 비디오 클립들을 순서대로 연결하고 길이 맞추기
            final_video = self.concatenate_and_fit_duration(video_clips, target_duration)
            
            # 텍스트 오버레이 추가
            final_video_with_text = self.add_text_overlay(final_video, script, topic)
            
            # 오디오 추가
            final_video_with_audio = final_video_with_text.set_audio(audio_clip)
            
            # 최종 효과 추가
            final_video_enhanced = self.add_visual_effects(final_video_with_audio)
            
            # 출력 파일 경로
            output_path = f"/tmp/youtube_shorts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            
            # 비디오 렌더링
            final_video_enhanced.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile_path="/tmp/temp_audio.m4a",
                remove_temp=True,
                preset='medium',
                ffmpeg_params=['-crf', '23']
            )
            
            # 메모리 정리
            audio_clip.close()
            for clip in video_clips:
                clip.close()
            final_video_enhanced.close()
            
            logger.info(f"✅ YouTube Shorts 비디오 생성 완료: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ 비디오 생성 실패: {str(e)}")
            return None
    
    def crop_to_vertical(self, clip):
        """비디오를 9:16 세로 비율로 크롭"""
        try:
            w, h = clip.size
            target_ratio = 9/16
            current_ratio = w/h
            
            if current_ratio > target_ratio:
                # 너무 넓음 - 좌우 크롭
                new_width = int(h * target_ratio)
                x_center = w // 2
                x1 = x_center - new_width // 2
                x2 = x_center + new_width // 2
                cropped = clip.crop(x1=x1, x2=x2)
            else:
                # 너무 높음 - 상하 크롭
                new_height = int(w / target_ratio)
                y_center = h // 2
                y1 = y_center - new_height // 2
                y2 = y_center + new_height // 2
                cropped = clip.crop(y1=y1, y2=y2)
            
            # 최종 해상도로 리사이즈
            resized = cropped.resize((self.output_width, self.output_height))
            
            return resized
            
        except Exception as e:
            logger.error(f"❌ 비디오 크롭 실패: {str(e)}")
            return clip.resize((self.output_width, self.output_height))
    
    def concatenate_and_fit_duration(self, video_clips, target_duration):
        """비디오 클립들을 연결하고 목표 길이에 맞추기"""
        try:
            # 클립들을 무작위로 섞기
            random.shuffle(video_clips)
            
            # 필요한 길이만큼 클립 선택 및 연결
            selected_clips = []
            current_duration = 0
            
            while current_duration < target_duration:
                for clip in video_clips:
                    if current_duration >= target_duration:
                        break
                    
                    remaining_time = target_duration - current_duration
                    if clip.duration <= remaining_time:
                        selected_clips.append(clip)
                        current_duration += clip.duration
                    else:
                        # 클립을 필요한 길이만큼 자르기
                        trimmed_clip = clip.subclip(0, remaining_time)
                        selected_clips.append(trimmed_clip)
                        current_duration += remaining_time
                        break
                
                if current_duration >= target_duration:
                    break
            
            # 클립들 연결
            if selected_clips:
                concatenated = concatenate_videoclips(selected_clips)
                return concatenated
            else:
                # 첫 번째 클립만 사용하고 길이 조정
                return video_clips[0].subclip(0, min(target_duration, video_clips[0].duration))
                
        except Exception as e:
            logger.error(f"❌ 비디오 연결 실패: {str(e)}")
            return video_clips[0].subclip(0, min(target_duration, video_clips[0].duration))
    
    def add_text_overlay(self, video_clip, script, topic):
        """텍스트 오버레이 추가"""
        try:
            # 대본에서 주요 문장 추출
            sentences = self.extract_key_sentences(script)
            
            # 텍스트 클립들 생성
            text_clips = []
            
            # 제목 텍스트 (처음 3초)
            title_text = topic[:30] + "..." if len(topic) > 30 else topic
            title_clip = self.create_text_clip(
                text=title_text,
                fontsize=60,
                color='white',
                stroke_color='black',
                stroke_width=3,
                duration=3,
                position=('center', 'top'),
                start_time=0
            )
            text_clips.append(title_clip)
            
            # 핵심 문장들을 시간대별로 배치
            if sentences:
                duration_per_sentence = (video_clip.duration - 3) / len(sentences)
                
                for i, sentence in enumerate(sentences):
                    start_time = 3 + (i * duration_per_sentence)
                    sentence_clip = self.create_text_clip(
                        text=sentence,
                        fontsize=45,
                        color='yellow',
                        stroke_color='black',
                        stroke_width=2,
                        duration=min(duration_per_sentence + 1, 4),  # 최대 4초
                        position=('center', 'center'),
                        start_time=start_time
                    )
                    text_clips.append(sentence_clip)
            
            # CTA 텍스트 (마지막 3초)
            cta_text = "👍 구독 & 좋아요!"
            cta_clip = self.create_text_clip(
                text=cta_text,
                fontsize=50,
                color='red',
                stroke_color='white',
                stroke_width=2,
                duration=3,
                position=('center', 'bottom'),
                start_time=max(0, video_clip.duration - 3)
            )
            text_clips.append(cta_clip)
            
            # 모든 텍스트 클립을 비디오에 합성
            final_video = CompositeVideoClip([video_clip] + text_clips)
            
            return final_video
            
        except Exception as e:
            logger.error(f"❌ 텍스트 오버레이 실패: {str(e)}")
            return video_clip
    
    def create_text_clip(self, text, fontsize, color, stroke_color, stroke_width, duration, position, start_time):
        """텍스트 클립 생성"""
        try:
            # 텍스트를 여러 줄로 나누기
            words = text.split()
            lines = []
            current_line = []
            max_chars_per_line = 20
            
            for word in words:
                if len(' '.join(current_line + [word])) <= max_chars_per_line:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            final_text = '\n'.join(lines)
            
            # TextClip 생성
            if os.path.exists(self.font_path):
                txt_clip = TextClip(
                    final_text,
                    fontsize=fontsize,
                    color=color,
                    font=self.font_path,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width,
                    method='caption',
                    align='center'
                ).set_duration(duration).set_start(start_time).set_position(position)
            else:
                # 기본 폰트 사용
                txt_clip = TextClip(
                    final_text,
                    fontsize=fontsize,
                    color=color,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width,
                    method='caption',
                    align='center'
                ).set_duration(duration).set_start(start_time).set_position(position)
            
            return txt_clip
            
        except Exception as e:
            logger.error(f"❌ 텍스트 클립 생성 실패: {str(e)}")
            return None
    
    def extract_key_sentences(self, script):
        """대본에서 핵심 문장 추출"""
        try:
            # 특수 문자 제거
            clean_script = script.replace('[훅]', '').replace('[메인 내용]', '').replace('[마무리/CTA]', '').replace('[마무리]', '')
            
            # 문장 분리
            sentences = [s.strip() for s in clean_script.split('.') if s.strip()]
            sentences = [s for s in sentences if len(s) > 10]  # 너무 짧은 문장 제외
            
            # 핵심 키워드가 포함된 문장 우선 선택
            keywords = ['방법', '비밀', '팁', '중요', '핵심', '성공', '수익', '돈']
            priority_sentences = []
            other_sentences = []
            
            for sentence in sentences:
                if any(keyword in sentence for keyword in keywords):
                    priority_sentences.append(sentence)
                else:
                    other_sentences.append(sentence)
            
            # 최대 4개 문장 선택
            final_sentences = (priority_sentences + other_sentences)[:4]
            
            return final_sentences
            
        except Exception as e:
            logger.error(f"❌ 핵심 문장 추출 실패: {str(e)}")
            return []
    
    def add_visual_effects(self, video_clip):
        """비주얼 효과 추가"""
        try:
            # 밝기 및 대비 조정
            enhanced_video = video_clip.fx(colorx, 1.1)  # 약간 밝게
            
            # 페이드 인/아웃 효과
            enhanced_video = enhanced_video.fadein(0.5).fadeout(0.5)
            
            return enhanced_video
            
        except Exception as e:
            logger.error(f"❌ 비주얼 효과 적용 실패: {str(e)}")
            return video_clip
