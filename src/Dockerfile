# 2025년 기준 최신 안정화 버전 사용
FROM python:3.11-slim-bookworm

# APT 소스 최신화 (에러 방지)
RUN echo "deb http://deb.debian.org/debian bookworm main non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list

# 필수 시스템 패키지 (FFmpeg 6.1 포함)
RUN apt-get update -y --fix-missing && \
    apt-get install -y --no-install-recommends \
    ffmpeg=7:6.1.1-3 \
    libsm6=2:1.2.3-1 \
    libxext6=2:1.3.4-1+b1 \
    libglib2.0-0=2.76.4-1 \
    wget=1.21.3-1+b2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ExifTool 직접 설치 (공식 최신 버전)
RUN wget https://exiftool.org/Image-ExifTool-13.25.tar.gz && \
    tar -xzf Image-ExifTool-*.tar.gz && \
    cd Image-ExifTool-* && \
    make install && \
    cd .. && \
    rm -rf Image-ExifTool-*

# 파이썬 가상환경 설정
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# 의존성 먼저 설치 (레이어 캐싱 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run 호환 포트 설정
ENV PORT=8080
EXPOSE 8080

# Graceful Shutdown 설정
STOPSIGNAL SIGTERM

# 헬스체크 엔드포인트 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
  CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "300"]
