import os
import logging
from PIL import Image, ImageDraw, ImageFont
import tempfile
import subprocess # subprocess 임포트

logger = logging.getLogger(__name__)

def generate_thumbnail(video_path, title_text="AI 자동 생성 영상"):
    """
    동영상에서 첫 프레임을 추출하고 텍스트를 추가하여 썸네일을 생성합니다.
    고양이체.ttf 폰트를 사용합니다.
    """
    if not os.path.exists(video_path):
        logger.error(f"썸네일 생성 실패: 원본 영상 파일이 존재하지 않습니다. {video_path}")
        return None

    temp_dir = tempfile.mkdtemp()
    thumbnail_raw_path = os.path.join(temp_dir, "temp_thumbnail_raw.jpg")
    thumbnail_final_path = os.path.join(temp_dir, "temp_thumbnail.jpg")

    try:
        # 1. FFmpeg로 첫 프레임 추출
        # -ss 00:00:01 (1초 지점), -vframes 1 (1프레임만 추출), -q:v 2 (품질)
        cmd_extract_frame = [
            "ffmpeg",
            "-i", video_path,
            "-ss", "00:00:01",
            "-vframes", "1",
            "-q:v", "2",
            "-y", # 덮어쓰기 허용
            thumbnail_raw_path
        ]
        result = subprocess.run(cmd_extract_frame, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            logger.error(f"썸네일 프레임 추출 FFmpeg 오류: {result.stderr}")
            return None

        if not os.path.exists(thumbnail_raw_path):
            logger.error(f"썸네일 프레임 추출 실패: {thumbnail_raw_path} 파일이 생성되지 않았습니다.")
            return None
            
        # 2. 텍스트 추가 (Pillow 사용)
        img = Image.open(thumbnail_raw_path)
        draw = ImageDraw.Draw(img)
        
        # 폰트 로드 (고양이체.ttf)
        font_path = "fonts/Catfont.ttf" # 폰트 경로 (프로젝트 루트의 fonts 폴더에 폰트를 넣을 예정)
        # 만약 fonts/Catfont.ttf가 없으면 기본 폰트 사용 (한글 지원 폰트)
        try:
            # Dockerfile에 Noto Sans CJK KR 폰트를 설치했으므로, 우선적으로 해당 폰트를 시도
            # 또는 시스템에 설치된 폰트 중 하나를 지정
            font = ImageFont.truetype(font_path, 80) # 폰트 크기 조정
            logger.info(f"'{font_path}' 폰트 로드 성공.")
        except IOError:
            logger.warning(f"⚠️ 폰트 '{font_path}'를 찾을 수 없습니다. 기본 폰트 또는 Noto Sans CJK KR을 시도합니다.")
            try:
                # 시스템에 설치된 한글 지원 폰트 (예: NotoSansKR-Regular.ttf 또는 Arial.ttf)
                # 실제 배포 환경의 폰트 경로를 확인하여 적절히 수정 필요
                font = ImageFont.truetype("NotoSansKR-Regular.ttf", 80) # Linux 환경 경로
                logger.info("NotoSansKR-Regular.ttf 폰트 로드 성공.")
            except IOError:
                logger.warning("⚠️ NotoSansKR-Regular.ttf 폰트도 찾을 수 없습니다. 기본 Arial 폰트 사용.")
                font = ImageFont.truetype("arial.ttf", 80) # Windows 환경 기본 폰트
        except Exception as font_e:
            logger.error(f"폰트 로드 중 알 수 없는 오류 발생: {font_e}")
            font = ImageFont.truetype("arial.ttf", 80) # 최후의 수단으로 Arial
            
        # 텍스트 위치 및 색상
        text_color = "yellow"
        stroke_color = "black"
        stroke_width = 3

        # 텍스트 윤곽선 그리기 (테두리 효과)
        for x_offset in [-stroke_width, 0, stroke_width]:
            for y_offset in [-stroke_width, 0, stroke_width]:
                if x_offset == 0 and y_offset == 0:
                    continue
                draw.text((10 + x_offset, 10 + y_offset), title_text, fill=stroke_color, font=font)
        
        # 실제 텍스트 그리기
        draw.text((10, 10), title_text, fill=text_color, font=font)
        
        img.save(thumbnail_final_path)
        logger.info(f"썸네일 생성 완료: {thumbnail_final_path}")
        return thumbnail_final_path
    except FileNotFoundError:
        logger.error("FFmpeg이 설치되어 있지 않거나 PATH에 없습니다. Dockerfile 확인 필요.")
        return None
    except Exception as e:
        logger.error(f"썸네일 생성 중 예외 발생: {str(e)}\n{traceback.format_exc()}")
        return None
    finally:
        # 원본 추출 이미지 삭제
        if os.path.exists(thumbnail_raw_path):
            os.remove(thumbnail_raw_path)
            logger.info(f"��️ 임시 썸네일 원본 파일 삭제: {thumbnail_raw_path}")
