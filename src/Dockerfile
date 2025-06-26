# 파이썬 공식 이미지 사용 (작은 용량을 위해 slim 버전을 권장)
FROM python:3.11-slim-buster

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (필요한 경우)
# 이 부분은 필요에 따라 추가될 수 있습니다. (예: video_creator에 필요한 라이브러리)
# Cloud Run 환경은 많은 기본 라이브러리를 포함하고 있으므로, 대부분의 경우 추가 의존성은 불필요합니다.
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     ffmpeg \
#     # 필요한 다른 라이브러리 \
#     && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 설치
# 먼저 requirements.txt 파일을 복사하여 캐시 활용도를 높입니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 코드 복사
COPY . .

# Cloud Run이 요청을 보낼 포트를 환경 변수로 설정
ENV PORT 8080

# 애플리케이션 실행 명령
# Gunicorn을 사용하여 Flask 애플리케이션을 안정적으로 실행합니다.
# `-w 2`는 워커 프로세스 수 (CPU 코어 수의 2배 정도가 일반적)
# `--timeout 300`은 요청 타임아웃 (초), Cloud Run의 최대 요청 타임아웃은 60분
# `app:app`은 src/app.py 파일의 Flask 인스턴스 이름 (app.py 파일의 app 변수)
CMD exec gunicorn --bind 0.0.0.0:$PORT --worker-class gevent --workers 2 --timeout 540 app:app

# 또는 간단하게 Flask 내장 서버로 실행 (개발/테스트용으로는 괜찮지만 프로덕션에는 Gunicorn 권장)
# CMD python app.py
