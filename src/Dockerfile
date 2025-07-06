# Dockerfile (이전 내용을 모두 지우고 아래 내용으로 교체하세요!)

# Python 3.11 버전의 가벼운 이미지를 사용합니다.
FROM python:3.11-slim-buster

# ffmpeg, libimage-exiftool-perl, wget을 설치합니다.
# 이 도구들은 동영상 처리나 파일 다운로드에 필요해요.
RUN apt-get update && \
    apt-get install -y ffmpeg libimage-exiftool-perl wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 컨테이너 안에서 작업할 폴더를 /app으로 정합니다.
WORKDIR /app

# ✅ 중요! GitHub Actions에서 'docker build -t ... ./src' 라고 명령을 주면,
# Dockerfile은 'src' 폴더 안에서 실행되는 것처럼 동작해요.
# 그래서 'src/'를 붙이지 않고 바로 'requirements.txt'를 복사합니다.
COPY requirements.txt /app/requirements.txt

# /app/requirements.txt에 적힌 모든 파이썬 라이브러리를 설치합니다.
# --no-cache-dir: 설치할 때 임시 파일을 만들지 않아서 이미지 크기를 줄여줘요.
RUN pip install --no-cache-dir -r /app/requirements.txt

# ✅ 중요! 'src' 폴더 안의 모든 파일(현재 폴더)을 컨테이너의 '/app' 폴더로 복사합니다.
COPY . /app

# 이 앱이 8080번 포트로 통신할 거라고 알려줍니다.
EXPOSE 8080

# Gunicorn이라는 웹 서버로 Flask 앱을 실행합니다.
# --worker-class gevent: 동시에 여러 작업을 처리할 수 있게 해줘요. (API 호출처럼 기다려야 하는 작업에 좋아요)
# --workers 1: 동시에 1개의 작업만 처리합니다. (나중에 필요하면 늘릴 수 있어요)
# --timeout 0: 작업이 끝날 때까지 무한정 기다려줍니다. (주의: 실제 서비스에서는 적절한 시간 제한을 두는 게 좋아요)
# app:app은 /app 폴더 안에 있는 'app.py' 파일에서 'app'이라는 이름의 Flask 앱을 실행하라는 뜻입니다.
CMD ["gunicorn", "--worker-class", "gevent", "--workers", "1", "--timeout", "0", "app:app"]
