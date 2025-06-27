# src/Dockerfile
# Python 3.11 Slim 이미지 사용 (가장 안정적이고 경량)
FROM python:3.11-slim-buster

# ffmpeg 설치 (moviepy 사용을 위해 필수)
# Cloud Run 환경에서 필요한 패키지들을 설치합니다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    # 다른 필요한 시스템 라이브러리가 있다면 여기에 추가 (예: imagemagick)
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 파일 복사 (캐싱 활용을 위해 먼저 복사)
COPY requirements.txt .

# Python 종속성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Cloud Run이 Flask 애플리케이션을 실행할 포트 설정 (Cloud Run에 의해 자동 주입됨)
ENV PORT 8080

# Gunicorn을 사용하여 Flask 애플리케이션 실행
# --bind :$PORT : 0.0.0.0:${PORT}와 동일, 모든 네트워크 인터페이스에서 포트를 리스닝합니다.
# --workers 1 : 단일 워커 (Cloud Run 인스턴스당 하나의 컨테이너 프로세스)
# --timeout 0 : 요청 타임아웃을 무한대로 설정 (장시간 비동기 작업에 유용)
# main:app : src/main.py 파일 내의 'app' Flask 인스턴스를 찾아 실행하라는 의미입니다.
CMD exec gunicorn --bind :$PORT --workers 1 --timeout 0 main:app
