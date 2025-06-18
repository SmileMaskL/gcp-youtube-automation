FROM python:3.11-slim

# 필수 시스템 패키지 설치 (Gunicorn 의존성)
RUN apt-get update && apt-get install -y \
    gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Gunicorn 명시적 설치
RUN pip install --no-cache-dir gunicorn uvicorn
RUN pip install --no-cache-dir -r requirements.txt

# 포트 설정
EXPOSE 8080

# 실행 명령 (절대경로 사용)
CMD ["/usr/local/bin/gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8080", "--timeout", "120", "src.health:app"]
