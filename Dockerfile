FROM python:3.10-slim

# 필수 도구 설치
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# pip 업그레이드 먼저 수행
RUN pip install --upgrade pip

# requirements 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 실행 포트 설정
ENV PORT 8080

# 실행 명령
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
