# src/Dockerfile

# 멀티스테이지 빌드 적용
FROM python:3.11-bookworm AS builder

# 시스템 패키지 (빌드용)
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------------------
# 런타임 이미지
FROM python:3.11-slim-bookworm

# 런타임 패키지
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ffmpeg libsm6 libxext6 libglib2.0-0 libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리
WORKDIR /app

# requirements 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .

# 설치 전 src 폴더를 Python 경로에 추가
ENV PYTHONPATH=/app

# 포트 설정
ENV PORT=8080
EXPOSE 8080

# 실행 명령어
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "300"]
