# Python 3.10 기반 슬림 이미지 사용 (경량화)
FROM python:3.10-slim-buster

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 필수 패키지 설치 (ffmpeg: 영상 처리, libsm6/libxext6: OpenCV 의존성, libsndfile1: 오디오 처리)
# 설치 후 캐시 정리하여 이미지 크기 최소화
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 설치
# requirements.txt 복사 (캐시 활용을 위해 먼저 복사)
COPY requirements.txt .
# pip install --no-cache-dir: 캐시 사용하지 않아 이미지 크기 증가 방지
RUN pip install --no-cache-dir -r requirements.txt

# 폰트 복사 (Catfont.ttf 파일이 fonts/Catfont.ttf 경로에 존재해야 함)
# 폴더가 없으면 생성 후 복사
RUN mkdir -p /app/fonts
COPY fonts/Catfont.ttf /app/fonts/Catfont.ttf

# 모든 소스코드 복사
# src 디렉토리의 모든 파일과 하위 디렉토리를 /app/src로 복사
COPY src /app/src

# .env 파일은 로컬 개발용입니다.
# Cloud Run Jobs에서는 환경 변수를 직접 주입받으므로, Dockerfile에 .env 파일을 복사할 필요가 없습니다.
# 하지만 로컬 테스트를 위해 .env 파일이 존재할 경우 복사하는 라인을 포함할 수 있습니다.
# GitHub Actions에서는 .env 파일을 컨테이너에 넣지 않습니다.
# COPY .env /app/.env # 주석 처리 또는 제거

# Cloud Run Job이 시작될 때 실행될 명령어
# src/batch_processor.py 스크립트를 Python 모듈로 실행
# 이 스크립트는 모든 자동화 작업을 순차적으로 수행합니다.
CMD ["python", "-m", "src.batch_processor"]
