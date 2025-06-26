# 수정된 파일: src/Dockerfile

# Python 3.9 (Cloud Run 권장 버전)
FROM python:3.9-slim-buster

# 작업 디렉토리 설정
WORKDIR /app

# 시스템에 필요한 패키지 설치 (예: FFmpeg for video processing)
# 주의: Cloud Run 환경에서는 추가 패키지 설치가 이미지 크기와 빌드 시간을 증가시킬 수 있습니다.
# RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
#     && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 코드 복사
COPY . .

# Cloud Run이 Flask 애플리케이션을 실행할 포트 설정
ENV PORT 8080

# Gunicorn을 사용하여 Flask 애플리케이션 실행
# --timeout 0: 요청 타임아웃을 무한대로 설정 (장시간 비동기 작업에 유용)
# --workers 1: 단일 워커 (Cloud Run 인스턴스당 하나의 컨테이너 프로세스)
CMD exec gunicorn --bind :$PORT --workers 1 --timeout 0 app:app
