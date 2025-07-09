FROM python:3.11-slim-buster

# 필수 패키지 설치
# buster 대신 bullseye나 bookworm과 같은 최신 Debian 버전을 고려할 수 있습니다.
# apt-get update && apt-get install 시 -y 옵션을 사용하여 사용자 확인 없이 설치를 진행합니다.
# --no-install-recommends 옵션은 권장 패키지를 설치하지 않아 이미지 크기를 줄입니다.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libimage-exiftool-perl \
        wget \
        # 필요한 경우 추가 패키지 (예: git, openssh-client 등)
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 애플리케이션 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 의존성 설치
# pip install --no-cache-dir: 캐시를 사용하지 않아 이미지 크기를 줄입니다.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
# .dockerignore 파일을 활용하여 불필요한 파일은 이미지에 포함되지 않도록 합니다.
COPY . .

# Cloud Run은 PORT 환경 변수를 자동으로 주입하므로, 굳이 Dockerfile에서 EXPOSE를 명시하지 않아도 됩니다.
# 하지만 명시적으로 8080을 사용하겠다는 의지를 나타내는 것은 좋습니다.
EXPOSE 8080

# 애플리케이션 시작 명령
# Cloud Run은 PORT 환경 변수를 자동으로 제공합니다.
# Gunicorn을 사용하여 Uvicorn을 실행하면 더 안정적이고 프로덕션에 적합합니다.
# worker-class는 gevent를 사용하여 비동기 작업을 효율적으로 처리합니다.
# PORT 환경 변수를 직접 사용하도록 설정합니다.
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app:app", "--bind", "0.0.0.0:${PORT}"]
