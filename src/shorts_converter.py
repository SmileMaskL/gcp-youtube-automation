import os
import logging

logger = logging.getLogger(__name__)

def convert_to_shorts(video_path):
    """
    영상을 9:16 비율의 YouTube Shorts 형식으로 변환합니다.
    원본 영상이 이미 해당 비율이거나 변환이 불필요한 경우 원본 경로를 반환합니다.
    """
    if not os.path.exists(video_path):
        logger.error(f"Shorts 변환 실패: 원본 영상 파일이 존재하지 않습니다. {video_path}")
        return video_path # 원본이 없으면 변환 불가

    output_dir = os.path.dirname(video_path)
    output_filename = os.path.basename(video_path).replace('.mp4', '_shorts.mp4')
    output_path = os.path.join(output_dir, output_filename)

    try:
        # FFmpeg를 사용하여 영상 비율을 9:16으로 자르고, 오디오는 복사
        # -vf "scale=-1:1920,crop=1080:1920" 또는 "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
        # Shorts 권장 해상도 1080x1920 (9:16)
        # crop=ih*9/16:ih: (세로를 기준으로 가로를 9:16으로 자름)
        # scale=1080:-1: (가로를 1080으로 맞추고 세로는 비율 유지)
        # pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black (여백 추가)
        # 여기서는 가장 간단한 중앙 크롭 방식 사용
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", "crop=ih*9/16:ih", # 가로를 세로의 9/16으로 중앙 크롭
            "-c:v", "libx264", # 비디오 코덱 지정 (안정성)
            "-preset", "fast", # 인코딩 속도 (low-spec PC 고려)
            "-crf", "23", # 품질 (낮을수록 고품질)
            "-c:a", "aac", # 오디오 코덱 지정
            "-b:a", "128k", # 오디오 비트레이트
            "-y", # 덮어쓰기 허용
            output_path
        ]
        
        # os.system 대신 subprocess를 사용하여 안정성 향상 및 에러 확인
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            logger.error(f"Shorts 변환 FFmpeg 오류: {result.stderr}")
            return video_path # 변환 실패 시 원본 반환
        
        logger.info(f"Shorts 변환 성공: {output_path}")
        return output_path
    except FileNotFoundError:
        logger.error("FFmpeg이 설치되어 있지 않거나 PATH에 없습니다. Dockerfile 확인 필요.")
        return video_path
    except Exception as e:
        logger.error(f"Shorts 변환 중 예외 발생: {str(e)}\n{traceback.format_exc()}")
        return video_path # 실패 시 원본 반환
