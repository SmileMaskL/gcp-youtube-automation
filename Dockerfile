FROM python:3.11-slim

WORKDIR /app

# 시스템 종속성 (한글 폰트 포함)
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 wget curl \
    && wget -O /usr/share/fonts/NanumGothic.ttf \
       https://github.com/naver/nanumfont/raw/master/fonts/NanumGothic.ttf \
    && rm -rf /var/lib/apt/lists/*

# 의존성 먼저 설치 (빌드 캐시 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY . .

# 환경 변수 설정
ARG GCP_PROJECT_ID
ENV GCP_PROJECT_ID=${GCP_PROJECT_ID}
ENV PYTHONPATH=/app
ENV PORT=8080

# 디렉토리 생성
RUN mkdir -p /app/temp /app/outputs

# 헬스체크
HEALTHCHECK --interval=30s --timeout=60s \
    CMD curl -f http://localhost:8080/health || exit 1

# 실행 명령 (Gunicorn + Uvicorn)
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8080", "--timeout", "120", "src.health:app"]
