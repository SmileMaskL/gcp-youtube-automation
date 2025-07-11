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

# 작업 디렉토리 설정
# 호스트의 'src' 디렉토리 내용이 컨테이너의 '/app/src'로 복사될 것입니다.
WORKDIR /app/src

# requirements 설치
# Dockerfile이 src 디렉토리 내에 있고, requirements.txt도 src 디렉토리 내에 있으므로
# 현재 작업 디렉토리(./)에서 requirements.txt를 찾습니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
# 호스트의 현재 빌드 컨텍스트(즉, src 디렉토리)의 모든 내용을
# 컨테이너의 현재 작업 디렉토리인 /app/src로 복사합니다.
COPY . .

# Python 경로에 /app/src 폴더를 추가
# 이렇게 하면 /app/src/app.py에서 /app/src/youtube_uploader.py 등을
# 'from youtube_uploader import ...' 형태로 직접 임포트할 수 있습니다.
ENV PYTHONPATH=/app/src # <--- 주석을 별도의 줄로 분리했습니다.

# 포트 설정
ENV PORT=8080
EXPOSE 8080

# 실행 명령어
# Uvicorn은 /app/src 디렉토리에서 app.py 파일을 찾아 그 안의 'app' 객체를 실행합니다.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "300"]
