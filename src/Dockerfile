# src/Dockerfile

# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y ffmpeg libimage-exiftool-perl wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치 (캐시 최적화)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . ./

# 기본 이미지 제공
RUN if [ ! -f "default_image.jpg" ]; then \
        echo "default_image.jpg not found, downloading a placeholder image..."; \
        wget -O default_image.jpg https://via.placeholder.com/1920x1080.png?text=Default+Thumbnail; \
    fi

# 환경 변수 설정
ENV PORT=8080
ENV MAX_WORKERS=4
ENV ENABLE_GCS_BACKUP="false" 

# Gunicorn 실행 (JSON 배열 형식 권장)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
