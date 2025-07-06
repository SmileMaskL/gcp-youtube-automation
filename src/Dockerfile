# Dockerfile (새로 생성하거나 기존 내용을 전부 교체하세요!)

# Python 3.11 버전의 경량 이미지를 사용합니다.
FROM python:3.11-slim-buster

# ffmpeg, libimage-exiftool-perl, wget 설치
# YouTube Shorts 제작에 필요한 도구들입니다.
# ffmpeg: 동영상 처리
# libimage-exiftool-perl: 이미지 메타데이터 처리 (필요시)
# wget: 파일 다운로드
RUN apt-get update && \
    apt-get install -y ffmpeg libimage-exiftool-perl wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 컨테이너 내부의 작업 디렉토리를 /app으로 설정합니다.
WORKDIR /app

# requirements.txt 파일을 /app 디렉토리로 복사합니다.
# 주의: GitHub Actions에서 docker build -t ... ./src 로 빌드하므로,
# Dockerfile이 src 디렉토리 안에서 실행되는 것처럼 보이지만,
# 실제로는 GitHub 저장소의 루트에서 src 디렉토리를 빌드 컨텍스트로 사용하므로,
# Dockerfile 내에서는 src/ 를 붙이지 않고 바로 requirements.txt를 참조합니다.
COPY requirements.txt /app/requirements.txt

# /app/requirements.txt에 있는 모든 파이썬 라이브러리를 설치합니다.
# --no-cache-dir: 캐시를 사용하지 않아 이미지 크기를 줄입니다.
RUN pip install --no-cache-dir -r /app/requirements.txt

# ✅ 전체 코드 복사
# 프로젝트의 모든 파일(src 디렉토리 안의 파일들)을 컨테이너의 /app 디렉토리로 복사합니다.
# GitHub Actions에서 './src'를 빌드 컨텍스트로 사용했기 때문에,
# 이 Dockerfile이 src 디렉토리 내부에 있다고 가정하고 상대 경로 '.'를 사용합니다.
COPY . /app

# Flask 애플리케이션이 8080 포트에서 실행될 것임을 알립니다.
EXPOSE 8080

# Gunicorn을 사용하여 Flask 애플리케이션을 실행합니다.
# --worker-class gevent: 비동기 처리를 위해 gevent 워커를 사용합니다. (API 호출 등 I/O 작업에 유리)
# --workers 1: 워커 수를 1개로 설정합니다. (필요에 따라 늘릴 수 있습니다)
# --timeout 0: 요청 타임아웃을 무제한으로 설정합니다. (주의: 불안정할 수 있으니 프로덕션에서는 적절히 설정)
# app:app은 /app 디렉토리 내의 app.py 파일에서 Flask 앱 인스턴스 이름이 'app'임을 의미합니다.
CMD ["gunicorn", "--worker-class", "gevent", "--workers", "1", "--timeout", "0", "app:app"]
