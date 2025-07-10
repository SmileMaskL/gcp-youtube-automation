# src/Dockerfile
# 멀티스테이지 빌드 적용
# 이 builder 스테이지는 ExifTool 빌드에 사용되었으나, 현재는 ExifTool이 제거되었으므로
# 필요한 경우에만 사용하거나 제거해도 무방합니다.
# 현재는 런타임 이미지에 필요한 패키지 설치를 위해 builder 스테이지를 비워둡니다.
FROM python:3.11-bookworm AS builder

# 1. 시스템 패키지 (빌드용)
# ExifTool 빌드에 필요했던 build-essential, wget, perl 등은 제거합니다.
# 만약 다른 빌드 도구가 필요하다면 여기에 추가할 수 있습니다.
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    # 예: git (소스 코드 다운로드 등 필요시)
    && rm -rf /var/lib/apt/lists/*

# ----------------------------------------
# 런타임 이미지
FROM python:3.11-slim-bookworm

# 3. 런타임 패키지
# 애플리케이션 실행에 필요한 패키지들을 설치합니다.
# ffmpeg, libsm6, libxext6, libglib2.0-0, libgl1-mesa-glx 등은 비디오 처리에 필요할 수 있습니다.
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ffmpeg libsm6 libxext6 libglib2.0-0 libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리를 /app으로 설정
WORKDIR /app

# requirements.txt 파일을 복사하고 파이썬 종속성 설치
# --no-cache-dir 옵션으로 캐시를 사용하지 않아 이미지 크기를 줄입니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 애플리케이션 코드를 /app 디렉토리로 복사
# Dockerfile이 src/ 안에 있으므로, src/ 내부의 모든 파일을 복사합니다.
COPY . .

# Cloud Run이 애플리케이션을 실행할 포트 설정
ENV PORT=8080
EXPOSE 8080

# 애플리케이션 시작 명령어
# uvicorn을 사용하여 FastAPI 앱을 실행합니다.
# app:app은 src/app.py 파일 내의 app 인스턴스를 의미합니다.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "300"]
