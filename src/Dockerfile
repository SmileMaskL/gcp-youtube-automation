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
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 모든 소스 코드 복사 (src 디렉토리의 내용이 /app으로 복사됨)
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
# 'src.app'은 /app/src/app.py 모듈을 의미
# 'app'은 app.py 내의 Flask 애플리케이션 인스턴스 이름
# 현재 Dockerfile에서 WORKDIR이 /app이므로,
# src/app.py는 Docker 이미지 내에서 /app/src/app.py에 해당합니다.
# 따라서 gunicorn은 모듈 경로를 'src.app'으로 찾아야 합니다.
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "src.app:app"]
