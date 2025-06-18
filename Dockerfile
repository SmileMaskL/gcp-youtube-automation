FROM python:3.11-slim

WORKDIR /app

# 시스템 종속성 (한글 폰트 포함)
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 wget curl fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY . .

# 환경 변수 설정
ARG GCP_PROJECT_ID
ENV GCP_PROJECT_ID=${GCP_PROJECT_ID}
ENV PYTHONPATH=/app

# Cloud Run은 자동으로 PORT=8080을 설정하므로 주석 처리
# ENV PORT=8080

# 디렉토리 생성
RUN mkdir -p /app/temp /app/outputs

# 헬스체크
HEALTHCHECK --interval=30s --timeout=60s \
    CMD curl -f http://localhost:8080/health || exit 1

# 실행 명령 (Gunicorn + Uvicorn)
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8080", "--timeout", "120", "src.health:app"]
