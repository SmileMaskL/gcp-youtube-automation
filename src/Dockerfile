# src/Dockerfile

# Python 3.11 기반 슬림 이미지 사용
FROM python:3.11-slim-buster

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# 작업 디렉토리 설정
# 이 Dockerfile은 src/ 안에 있으므로, COPY . /app 은 src/의 모든 내용을 /app으로 복사합니다.
WORKDIR /app

# 시스템 패키지 설치 (ffmpeg, git, fontconfig, libfreetype6-dev)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    fontconfig \
    libfreetype6-dev \
    libsm6 \
    libxext6 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Python 종속성 설치
# Dockerfile이 src/ 안에 있으므로 requirements.txt는 . (현재 디렉토리)에 있습니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 폰트 디렉토리 생성 및 폰트 복사
# 폰트도 src/fonts/ 에 있다고 가정 (즉, Dockerfile 기준 ./fonts/)
RUN mkdir -p /app/fonts
COPY fonts/Catfont.ttf /app/fonts/Catfont.ttf

# 애플리케이션 소스 코드 복사 (src 폴더 전체를 /app으로 복사)
# Dockerfile이 src/ 안에 있으므로, src/의 모든 파일들을 /app으로 복사합니다.
COPY . /app/

# Cloud Functions는 entrypoint를 gcloud 명령으로 지정하므로 CMD나 ENTRYPOINT를 명시하지 않습니다.
# main.py의 trigger_youtube_upload 함수가 entrypoint가 됩니다.
ENV FUNCTION_TARGET=trigger_youtube_upload
