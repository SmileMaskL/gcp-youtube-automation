# src/Dockerfile
# Python 3.11 Slim 이미지 사용 (경량)
FROM python:3.11-slim-buster

# ffmpeg 설치 (moviepy 사용을 위해 필수)
# Cloud Run 환경에서 필요한 패키지들을 설치합니다.
RUN apt-get update && apt-get install -y \
    ffmpeg \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 파일 복사 (캐싱 활용을 위해 먼저 복사)
COPY requirements.txt .

# Python 종속성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 환경 변수 PORT를 Cloud Run이 주입합니다.
# Cloud Run은 컨테이너가 이 PORT에서 요청을 수신 대기할 것을 기대합니다.
# 기본값은 8080입니다.
ENV PORT 8080

# Flask 애플리케이션 실행 명령어
# Gunicorn을 사용하여 Flask 앱을 안정적으로 실행합니다.
# --bind 0.0.0.0:${PORT}는 어떤 IP에서든 PORT 환경 변수에 지정된 포트를 수신 대기하라는 의미입니다.
# main:app은 main.py 파일 내의 'app' Flask 인스턴스를 찾아 실행하라는 의미입니다.
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "main:app"]
