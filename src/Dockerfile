# 2025년 기준 Python 3.11 안정화 slim-bookworm 이미지 사용
FROM python:3.11-slim-bookworm

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    wget \
    curl \
    make \
    perl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ExifTool 설치 (최신 안정화 버전)
RUN wget https://exiftool.org/Image-ExifTool-12.74.tar.gz && \
    tar -xzf Image-ExifTool-12.74.tar.gz && \
    cd Image-ExifTool-12.74 && \
    perl Makefile.PL && \
    make && \
    make test && \
    make install && \
    cd .. && \
    rm -rf Image-ExifTool-12.74*

# 파이썬 가상환경 (권장)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# 의존성 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 앱 소스 복사
COPY . .

# Cloud Run 호환 포트
ENV PORT=8080
EXPOSE 8080

# Graceful shutdown
STOPSIGNAL SIGTERM

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# 최종 실행 명령
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "300"]
