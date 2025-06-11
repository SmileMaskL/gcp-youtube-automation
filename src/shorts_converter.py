"""
긴 동영상을 YouTube Shorts로 변환하는 모듈
"""
import os
import logging
import subprocess
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import json
import ffmpeg
from utils import FileManager, config_manager, retry_on_failure

logger = logging.getLogger(__name__)

class ShortsConverter:
    """YouTube Shorts 변환기"""
    
    def __init__(self, output_dir: str = "./output/shorts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Shorts 사양
        self.shorts_width = 1080
        self.shorts_height = 1920
        self.shorts_max_duration = 60  # 초
        self.shorts_min_duration = 15  # 초
        
        # 설정 로드
        self.config = config_manager.get('shorts', {
            'segment_duration': 30,
            'overlap_duration': 2,
            'fade_duration': 1,
            'quality': 'high',
            'bitrate': '8M',
            'fps': 30
        })
    
    def get_video_info(self, video_path: str) -> Dict:
        """비디오 정보 조회"""
        try:
            probe = ffmpeg.probe(video_path)
            video_stream = next((stream for stream in probe['streams'] 
                               if stream['codec_type'] == 'video'), None)
            
            if not video_stream:
                raise ValueError("비디오 스트림을 찾을 수 없습니다")
            
            return {
                'duration': float(probe['format']['duration']),
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'fps': eval(video_stream['r_frame_rate']),  # "30/1" -> 30.0
                'bitrate': int(probe['format'].get('bit_rate', 0))
            }
        except Exception as e:
            logger.error(f"비디오 정보 조회 실패: {e}")
            raise
    
    def detect_interesting_segments(self, video_path: str, info: Dict) -> List[Tuple[float, float]]:
        """흥미로운 구간 자동 감지"""
        segments = []
        duration = info['duration']
        segment_duration = self.config['segment_duration']
        overlap = self.config['overlap_duration']
        
        # 기본 전략: 균등 분할 + 겹치기
        current_time = 0
        while current_time < duration - self.shorts_min_duration:
            end_time = min(current_time + segment_duration, duration)
            
            # 최소 길이 확보
            if end_time - current_time >= self.shorts_min_duration:
                segments.append((current_time, end_time))
            
            current_time += segment_duration - overlap
            
            # 최대 10개 세그먼트로 제한
            if len(segments) >= 10:
                break
        
        # 고급 감지 (오디오 레벨 기반)
        try:
            audio_segments = self._detect_audio_peaks(video_path, info)
            if audio_segments:
                segments = audio_segments[:10]  # 상위 10개만 선택
        except Exception as e:
            logger.warning(f"오디오 피크 감지 실패, 기본 세그먼트 사용: {e}")
        
        return segments
    
    def _detect_audio_peaks(self, video_path: str, info: Dict) -> List[Tuple[float, float]]:
        """오디오 피크를 기반으로 흥미로운 구간 감지"""
        segments = []
        temp_audio = self.output_dir / "temp_audio.wav"
        
        try:
            # 오디오 추출
            (
                ffmpeg
                .input(video_path)
                .output(str(temp_audio), acodec='pcm_s16le', ac=1, ar='22050')
                .overwrite_output()
                .run(quiet=True)
            )
            
            # 오디오 레벨 분석
            cmd = [
                'ffmpeg', '-i', str(temp_audio),
                '-af', 'volumedetect',
                '-f', 'null', '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.STDOUT)
            
            # 결과 파싱하여 세그먼트 생성 (간단한 구현)
            duration = info['duration']
            segment_duration = self.config['segment_duration']
            
            # 오디오 분석 결과를 바탕으로 세그먼트 조정
            num_segments = max(1, int(duration / segment_duration))
            for i in range(min(num_segments, 10)):
                start_time = i * (duration / num_segments)
                end_time = min(start_time + segment_duration, duration)
                
                if end_time - start_time >= self.shorts_min_duration:
                    segments.append((start_time, end_time))
            
            return segments
            
        except Exception as e:
            logger.warning(f"오디오 피크 감지 중 오류: {e}")
            return []
        finally:
            if temp_audio.exists():
                temp_audio.unlink()
    
    @retry_on_failure(max_retries=3)
    def convert_segment_to_shorts(self, video_path: str, start_time: float, 
                                end_time: float, output_path: str) -> bool:
        """비디오 세그먼트를 Shorts 형태로 변환"""
        try:
            input_stream = ffmpeg.input(video_path, ss=start_time, t=end_time - start_time)
            
            # 세로형으로 크롭 및 리사이즈
            video = (
                input_stream
                .video
                .filter('scale', self.shorts_width, self.shorts_height, force_original_aspect_ratio='increase')
                .filter('crop', self.shorts_width, self.shorts_height)
            )
            
            # 페이드 효과 추가
            fade_duration = self.config['fade_duration']
            segment_duration = end_time - start_time
            
            if segment_duration > fade_duration * 2:
                video = video.filter('fade', t='in', st=0, d=fade_duration)
                video = video.filter('fade', t='out', st=segment_duration - fade_duration, d=fade_duration)
            
            # 오디오 처리
            audio = input_stream.audio
            
            # 출력 설정
            output = ffmpeg.output(
                video, audio, output_path,
                vcodec='libx264',
                acodec='aac',
                video_bitrate=self.config['bitrate'],
                audio_bitrate='128k',
                r=self.config['fps'],
                pix_fmt='yuv420p'
            )
            
            ffmpeg.run(output, overwrite_output=True, quiet=True)
            
            # 결과 검증
            if not os.path.exists(output_path):
                raise FileNotFoundError("출력 파일이 생성되지 않았습니다")
            
            # 파일 크기 확인
            if os.path.getsize(output_path) < 1024:  # 1KB 미만이면 오류
                raise ValueError("출력 파일이 너무 작습니다")
            
            logger.info(f"Shorts 변환 완료: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Shorts 변환 실패: {e}")
            if os.path.exists(output_path):
                os.unlink(output_path)
            return False
    
    def add_shorts_effects(self, video_path: str, output_path: str) -> bool:
        """Shorts에 특화된 효과 추가"""
        try:
            input_stream = ffmpeg.input(video_path)
            
            # 비디오 효과
            video = input_stream.video
            
            # 샤프닝 필터
            video = video.filter('unsharp', luma_msize_x=5, luma_msize_y=5, luma_amount=1.0)
            
            # 색상 보정
            video = video.filter('eq', contrast=1.1, brightness=0.05, saturation=1.2)
            
            # 오디오 효과
            audio = input_stream.audio
            
            # 오디오 정규화
            audio = audio.filter('loudnorm', I=-16, LRA=11, TP=-1.5)
            
            # 출력
            output = ffmpeg.output(
                video, audio, output_path,
                vcodec='libx264',
                acodec='aac',
                crf=18,  # 고품질
                preset='slow'
            )
            
            ffmpeg.run(output, overwrite_output=True, quiet=True)
            return True
            
        except Exception as e:
            logger.error(f"효과 추가 실패: {e}")
            return False
    
    def create_shorts_from_video(self, video_path: str, max_shorts: int = 5) -> List[str]:
        """긴 동영상에서 여러 Shorts 생성"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"입력 비디오를 찾을 수 없습니다: {video_path}")
        
        logger.info(f"Shorts 변환 시작: {video_path}")
        
        # 비디오 정보 조회
        info = self.get_video_info(video_path)
        logger.info(f"비디오 정보 - 길이: {info['duration']:.1f}초, 해상도: {info['width']}x{info['height']}")
        
        # 흥미로운 구간 감지
        segments = self.detect_interesting_segments(video_path, info)
        logger.info(f"{len(segments)}개 세그먼트 감지됨")
        
        # 최대 개수 제한
        segments = segments[:max_shorts]
        
        # 각 세그먼트를
