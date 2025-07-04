# src/Dockerfile

FROM python:3.11-slim

# 필수 패키지 설치
RUN apt-get update && \
    apt-get install -y ffmpeg libimage-exiftool-perl wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리
WORKDIR /app

# requirements.txt 복사 및 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 모든 소스 복사
COPY . .

# default_image.jpg 없는 경우 placeholder 다운로드
RUN if [ ! -f "default_image.jpg" ]; then \
        wget -O default_image.jpg https://via.placeholder.com/1920x1080.png?text=Default+Thumbnail; \
    fi

# 환경 변수 설정
ENV PORT=8080
ENV MAX_WORKERS=4
ENV ENABLE_GCS_BACKUP="false"

# 🔥 Gunicorn으로 app.py의 app 객체 실행
# ⚠️ 여기서 'app:app' 은 app.py 파일 안의 Flask app 이름입니다.
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
