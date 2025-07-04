# src/Dockerfile

FROM python:3.11-slim

# 필수 시스템 패키지 설치 (ffmpeg 등)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libimage-exiftool-perl \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 의존성 복사 및 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스 복사
COPY . .

# 환경변수 기본값 설정 (필요에 따라 조정)
ENV PORT=8080
ENV MAX_THREADS=4
ENV ENABLE_GCS_BACKUP="false"

# gunicorn으로 실행 (4 worker, 0.0.0.0:PORT 바인딩)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
