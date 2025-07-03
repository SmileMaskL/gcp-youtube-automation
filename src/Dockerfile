# src/Dockerfile

# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 시스템 패키지 설치
# libimage-exiftool-perl은 moviepy의 내부 기능 (메타데이터 처리)에 필요할 수 있습니다.
# wget은 default_image.jpg 다운로드에 사용됩니다.
RUN apt-get update && \
    apt-get install -y ffmpeg libimage-exiftool-perl wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치 (캐시 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
# Dockerfile이 src/에 있고, docker build . 명령어를 src/에서 실행하므로,
# src/의 모든 내용이 /app으로 복사됩니다.
COPY . .

# 기본 이미지 제공: default_image.jpg가 없으면 다운로드
# 이 로직은 빌드 시점에 실행되므로, 이미지를 빌드할 때 항상 default_image.jpg가 있는지 확인하고 없으면 다운로드합니다.
# 이미지가 이미 src/ 디렉토리에 존재한다면 이 블록은 실행되지 않습니다.
RUN if [ ! -f "default_image.jpg" ]; then \
        echo "default_image.jpg not found, downloading a placeholder image..."; \
        wget -O default_image.jpg https://via.placeholder.com/1920x1080.png?text=Default+Thumbnail; \
    fi

# 환경 변수 설정
ENV PORT=8080
ENV MAX_WORKERS=4
ENV ENABLE_GCS_BACKUP="false" # GCS 백업 기능 사용 여부

# Gunicorn 실행 (프로덕션 최적화 설정)
# 쉘 형식 (CMD command arg1 arg2...)으로 환경 변수 확장
CMD gunicorn app:app \
    --bind 0.0.0.0:"$PORT" \
    --workers "$MAX_WORKERS" \
    --worker-class gthread \
    --threads 2 \
    --timeout 120
