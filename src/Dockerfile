<<<<<<< HEAD
# 1. 베이스 이미지 - Python 3.11 슬림 최신 안정화 버전
FROM python:3.11-slim-bookworm

# 2. apt 소스 리스트 정리 및 최신화
RUN echo "deb http://deb.debian.org/debian bookworm main non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list

# 3. 필수 시스템 패키지 설치 (FFmpeg 포함)
RUN apt-get update -y --fix-missing && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libsm6 \
        libxext6 \
        libglib2.0-0 \
        wget \
        perl \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 4. ExifTool 최신 버전 설치 (2025-07 기준 13.25 버전)
RUN wget https://exiftool.org/Image-ExifTool-13.25.tar.gz && \
    tar -xzf Image-ExifTool-13.25.tar.gz && \
    cd Image-ExifTool-13.25 && \
    perl Makefile.PL && \
    make && \
    make test && \
    make install && \
    cd .. && \
    rm -rf Image-ExifTool-13.25* 

# 5. Python 가상환경 생성 및 PATH 설정 (권장)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 6. 작업 디렉토리 설정
WORKDIR /app

# 7. requirements.txt 복사 및 패키지 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 8. 앱 소스 전체 복사
COPY . .

# 9. Cloud Run 호환 포트 설정
ENV PORT=8080
EXPOSE 8080

# 10. Graceful shutdown 시그널 설정
STOPSIGNAL SIGTERM

# 11. 헬스체크 엔드포인트 추가 (Cloud Run에서 권장)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# 12. uvicorn 서버 실행 명령어
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "300"]
=======
# src/Dockerfile
FROM python:3.11-slim-bullseye

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends gcc

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
>>>>>>> 39084fc7b559941b38b6aa3e14ae067a1e397f39
