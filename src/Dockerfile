# src/Dockerfile

# Python 3.11 slim base image
FROM python:3.11-slim-buster

# 필수 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libimage-exiftool-perl \
        wget \
        build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 빌드 도구 제거 (이미 설치된 wheel, cython 등 포함)
RUN apt-get purge -y build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 앱 코드 복사
COPY . .

# 8080 포트 노출
EXPOSE 8080

# uvicorn 단독 실행
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
