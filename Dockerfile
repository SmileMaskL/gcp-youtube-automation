FROM python:3.11-slim

WORKDIR /app

# 시스템 종속성 (한글 폰트 URL 수정)
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 wget curl fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY . .

# 환경 변수
ENV PYTHONPATH=/app
ENV PORT=8080  # Cloud Run과 호환되도록 설정

# 디렉토리 생성
RUN mkdir -p /app/temp /app/outputs

# 헬스체크
HEALTHCHECK --interval=30s --timeout=60s \
    CMD curl -f http://localhost:8080/health || exit 1

# 실행 명령 (Gunicorn + Uvicorn)
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8080", "--timeout", "120", "src.health:app"]
