FROM python:3.11-slim-bookworm

RUN echo "deb http://ftp.de.debian.org/debian bookworm main non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list

RUN rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    apt-get update -o Acquire::CompressionTypes::Order::=gz,bzip2,xz --fix-missing && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libsm6 \
        libxext6 \
        libglib2.0-0 \
        wget \
        curl \
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

# 5. 작업 디렉토리 설정
WORKDIR /app

# 6. requirements.txt 복사 및 패키지 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 7. 앱 소스 전체 복사
COPY . .

# 8. Cloud Run 환경변수 및 포트 설정
ENV PORT=8080
EXPOSE 8080

# 9. Graceful shutdown 시그널 설정
STOPSIGNAL SIGTERM

# 10. 헬스체크 엔드포인트 추가 (curl 설치했으니 문제없음)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# 11. uvicorn 서버 실행
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "300"]
