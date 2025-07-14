# src/Dockerfile

# 1. 베이스 이미지 - Python 3.11 슬림 최신 안정화 버전
FROM python:3.11-slim-bookworm

# 2. 필수 시스템 패키지 설치 (FFmpeg 포함)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        ffmpeg \
        libsm6 \
        libxext6 \
        libglib2.0-0 \
        wget \
        perl \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. ExifTool 설치 (예: 최신 안정 버전)
RUN wget https://exiftool.org/Image-ExifTool-12.73.tar.gz && \
    tar -xzf Image-ExifTool-12.73.tar.gz && \
    cd Image-ExifTool-12.73 && \
    perl Makefile.PL && \
    make && \
    make test && \
    make install && \
    cd .. && \
    rm -rf Image-ExifTool-12.73*

# 4. 작업 디렉토리 설정
WORKDIR /app

# 5. requirements.txt 복사 및 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. 앱 소스 전체 복사
COPY . .

# 7. Cloud Run 포트 설정
ENV PORT=8080
EXPOSE 8080

# 8. uvicorn 실행
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
