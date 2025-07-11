# src/Dockerfile
FROM python:3.11-slim-bookworm

# 1. 시스템 패키지
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 libglib2.0-0 libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 2. 작업 디렉토리
WORKDIR /app
COPY . .

# 3. Python 경로 설정
ENV PYTHONPATH="/app"

# 4. FFmpeg 설치
RUN cp bin/ffmpeg bin/ffprobe /usr/local/bin/

# 5. 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 6. 실행 명령 (절대경로 사용)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
