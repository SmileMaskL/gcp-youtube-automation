# src/Dockerfile

FROM python:3.11-slim-bookworm

# 필수 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 libglib2.0-0 libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app
COPY . .

# Python 경로 설정
ENV PYTHONPATH="/app"

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# FFmpeg 바이너리 복사
RUN cp bin/ffmpeg bin/ffprobe /usr/local/bin/

# 실행 명령어
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "300"]
