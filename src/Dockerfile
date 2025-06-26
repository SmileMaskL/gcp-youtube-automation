# Python 3.9 또는 3.10, 3.11 등 당신의 프로젝트에 맞는 안정적인 버전을 사용하세요.
# 여기서는 Python 3.11을 예시로 듭니다.
FROM python:3.11-slim-buster

# apt-get을 사용하기 전에 인덱스를 업데이트합니다.
RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 종속성 설치 (캐싱을 위해 먼저 복사)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Flask 애플리케이션이 실행될 포트 정의 (Cloud Run은 PORT 환경 변수를 사용)
ENV PORT 8080

# 컨테이너가 시작될 때 실행될 명령 (Flask 앱 실행)
# gunicorn은 Flask 앱을 프로덕션 환경에서 안정적으로 실행하기 위한 WSGI 서버입니다.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
