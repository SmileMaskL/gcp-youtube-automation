# Dockerfile (전체 코드 - Cloud Functions 2세대용으로 수정)
# Python 3.11 기반 이미지 사용
FROM python:3.11-slim-buster

# 환경 변수 설정 (Cloud Functions는 PORT를 자동으로 처리하므로 일반적으로 필요 없음)
ENV PYTHONUNBUFFERED 1

# 작업 디렉토리 설정
WORKDIR /app

# --- 다음 라인이 매우 중요합니다: FFmpeg 및 기타 시스템 패키지 설치 ---
# apt-get 업데이트 및 ffmpeg, git 설치
# --no-install-recommends 플래그는 불필요한 추천 패키지 설치를 방지하여 이미지 크기를 줄입니다.
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    # 폰트 렌더링에 필요한 추가 라이브러리가 있을 수 있습니다 (예: fontconfig, libfreetype6-dev).
    # Pillow가 이들을 필요로 할 수 있으므로 함께 설치합니다.
    fontconfig \
    libfreetype6-dev \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*
# ----------------------------------------------------------------------

# Python 종속성 설치
# src 폴더 안의 requirements.txt를 /app/src로 복사 후 설치
COPY src/requirements.txt /app/src/
RUN pip install --no-cache-dir -r /app/src/requirements.txt

# 폰트 디렉토리 생성 및 폰트 복사
# fonts/Catfont.ttf 파일이 프로젝트 루트의 fonts/Catfont.ttf 경로에 존재해야 함
RUN mkdir -p /app/fonts
COPY fonts/Catfont.ttf /app/fonts/

# 애플리케이션 소스 코드 복사 (src 폴더 전체를 /app/src로 복사)
COPY src/ /app/src/

# Cloud Functions는 entrypoint를 gcloud 명령으로 지정하므로 CMD나 ENTRYPOINT를 명시하지 않습니다.
# main.py의 youtube_automation_main 함수가 entrypoint가 됩니다.
