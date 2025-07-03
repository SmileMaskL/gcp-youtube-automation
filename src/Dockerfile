# src/Dockerfile

# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y ffmpeg libimage-exiftool-perl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치 (캐시 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 기본 이미지 제공
RUN if [ ! -f "default_image.jpg" ]; then \
        apt-get update && \
        apt-get install -y wget && \
        wget -O default_image.jpg https://via.placeholder.com/1920x1080.png?text=Default+Thumbnail && \
        apt-get purge -y wget && \
        apt-get autoremove -y; \
    fi

CMD ["gunicorn", "-w", "$MAX_WORKERS", "-b", "0.0.0.0:8080", "app:app"]

# 환경 변수 설정
ENV PORT=8080
ENV MAX_WORKERS=4
ENV ENABLE_GCS_BACKUP="false"

# Gunicorn 실행 (프로덕션 최적화 설정)
CMD ["gunicorn", "app:app", \
    "--bind", "0.0.0.0:8080", \
    "--workers", "$MAX_WORKERS", \
    "--worker-class", "gthread", \
    "--threads", "2", \
    "--timeout", "120"]
