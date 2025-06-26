# Dockerfile
# Python 3.11 기반 슬림 이미지 사용
FROM python:3.11-slim-buster

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치 (ffmpeg, git, fontconfig, libfreetype6-dev)
# --no-install-recommends 플래그는 불필요한 권장 패키지 설치를 방지하여 이미지 크기를 줄입니다.
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    fontconfig \
    libfreetype6-dev \
    # libsm6, libxext6는 MoviePy에서 종종 필요합니다. (MoviePy 버전에 따라 다를 수 있음)
    libsm6 \
    libxext6 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Python 종속성 설치
# 루트의 src 폴더 안의 requirements.txt를 /app/src/로 복사 후 설치
# 중요한 점: Dockerfile이 루트에 있고, src/requirements.txt를 바라봅니다.
COPY src/requirements.txt /app/src/requirements.txt
RUN pip install --no-cache-dir -r /app/src/requirements.txt

# 폰트 디렉토리 생성 및 폰트 복사
# fonts/Catfont.ttf 파일이 프로젝트 루트의 fonts/Catfont.ttf 경로에 존재해야 함
RUN mkdir -p /app/fonts
COPY fonts/Catfont.ttf /app/fonts/Catfont.ttf

# 애플리케이션 소스 코드 복사 (src 폴더 전체를 /app/src로 복사)
# 이 Dockerfile이 루트에 있으므로, src/ 디렉토리를 통째로 /app/src로 복사합니다.
COPY src/ /app/src/

# Cloud Functions는 entrypoint를 gcloud 명령으로 지정하므로 CMD나 ENTRYPOINT를 명시하지 않습니다.
# main.py의 trigger_youtube_upload 함수가 entrypoint가 됩니다.
# FUNCTIONS_FRAMEWORK_TARGET 환경 변수를 명시적으로 설정하여 함수의 진입점을 지정합니다.
ENV FUNCTION_TARGET=trigger_youtube_upload
