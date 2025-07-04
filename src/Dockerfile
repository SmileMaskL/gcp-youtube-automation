# src/Dockerfile

FROM python:3.11-slim

# 필요한 패키지 설치
RUN apt-get update && \
    apt-get install -y ffmpeg libimage-exiftool-perl wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리를 /app으로 설정
WORKDIR /app

# requirements.txt 복사 및 종속성 설치
# 현재 빌드 컨텍스트가 src 디렉토리이므로, requirements.txt는 .src/requirements.txt에 있습니다.
# 따라서 COPY requirements.txt ./ 는 src/requirements.txt를 /app/requirements.txt로 복사합니다.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 모든 소스 코드 복사 (빌드 컨텍스트가 ./src 이므로, src 디렉토리의 내용이 /app으로 복사됨)
# 즉, /app/app.py, /app/config.py 등등
COPY . .

# default_image.jpg가 없는 경우 다운로드
RUN if [ ! -f "default_image.jpg" ]; then \
        echo "default_image.jpg not found, downloading a placeholder image..."; \
        wget -O default_image.jpg https://via.placeholder.com/1920x1080.png?text=Default+Thumbnail; \
    fi

# 환경 변수 설정
ENV PORT=8080
ENV MAX_WORKERS=4
ENV ENABLE_GCS_BACKUP="false"

# Gunicorn을 사용하여 Flask 애플리케이션 실행
# WORKDIR이 /app이고, app.py가 /app/app.py로 복사되었으므로,
# Gunicorn은 'app' 모듈에서 'app' 객체를 찾습니다.
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
