# Python 3.11을 기반 이미지로 사용합니다.
FROM python:3.11-slim-buster

# FFmpeg 및 MoviePy/pydub에 필요한 라이브러리 설치
# (libsm6, libxext6는 MoviePy에서 필요한 경우가 많습니다.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 종속성 설치 (캐싱을 위해 먼저 requirements.txt 복사)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Flask 애플리케이션이 실행될 포트 정의 (Cloud Run은 PORT 환경 변수를 제공합니다.)
ENV PORT 8080

# 컨테이너가 시작될 때 실행될 명령 (Flask 앱을 gunicorn으로 실행)
# app:app은 app.py 파일의 Flask 애플리케이션 'app' 객체를 참조합니다.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
