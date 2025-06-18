FROM python:3.11-slim

# 1. 필수 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# 2. 명시적 Gunicorn 설치 (버전 고정)
RUN pip install --no-cache-dir gunicorn==21.2.0 uvicorn==0.29.0
RUN pip install --no-cache-dir -r requirements.txt

# 3. 포트 설정
EXPOSE 8080

# 4. 실행 명령 (절대경로 + 타임아웃 설정)
CMD ["/usr/local/bin/gunicorn", \
    "--bind", "0.0.0.0:8080", \
    "--timeout", "300", \
    "--workers", "1", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "src.health:app"]
