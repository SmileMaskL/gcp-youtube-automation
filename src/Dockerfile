# src/Dockerfile

FROM python:3.11-slim-bookworm

# 1. 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 libglib2.0-0 libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 2. 작업 디렉토리 설정
WORKDIR /app
ENV PYTHONPATH=/app

# 3. FFmpeg 바이너리 복사
COPY bin/ffmpeg bin/ffprobe /usr/local/bin/

# 4. 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스코드 복사
COPY . .

# 6. 실행 명령어
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
