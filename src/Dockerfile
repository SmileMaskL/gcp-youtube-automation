# src/Dockerfile

# --- 빌드 스테이지 ---
FROM python:3.11-bookworm AS builder

# 필수 빌드 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# --- 런타임 스테이지 ---
FROM python:3.11-slim-bookworm

# 필수 라이브러리 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsm6 libxext6 libglib2.0-0 libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# requirements 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .

# PYTHONPATH 설정 (src 모듈 인식)
ENV PYTHONPATH="${PYTHONPATH}:/app/src"

# 포트 설정
ENV PORT=8080
EXPOSE 8080

# uvicorn 실행 명령어 수정 (src.app:app 로 변경)
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "300"]
