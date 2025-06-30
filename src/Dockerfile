# src/Dockerfile

FROM python:3.11-slim-buster

# 시스템 라이브러리 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 파일 복사
COPY requirements.txt .

# pip 업그레이드 및 종속성 설치
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 기본 이미지 복사
COPY src/default_image.jpg /app/default_image.jpg

# 포트 설정
ENV PORT 8080

# gunicorn으로 앱 실행
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 0 --graceful-timeout 30 src.app:app
