# src/Dockerfile

# 1. 베이스 이미지 - Python 3.11 슬림 최신 안정화 버전
FROM python:3.11-slim-bookworm

# 2. 필수 시스템 패키지 설치 (FFmpeg 포함, ExifTool 포함)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        ffmpeg \
        libsm6 \
        libxext6 \
        libglib2.0-0 \
        wget \
        perl \
        build-essential \
        libimage-exiftool-perl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. requirements.txt 복사 및 패키지 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. 앱 소스 전체 복사
COPY . .

# 6. Cloud Run 호환 포트 설정
ENV PORT=8080
EXPOSE 8080

# 7. uvicorn 실행 (타임아웃 설정 필요 시 옵션 추가 가능)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
