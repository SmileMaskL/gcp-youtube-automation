FROM python:3.11-slim

WORKDIR /app

# 종속성 먼저 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 시스템 패키지 및 한글 폰트 설치
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 wget curl \
    && rm -rf /var/lib/apt/lists/* \
    && wget -O /usr/share/fonts/NanumGothic.ttf \
       https://github.com/naver/nanumfont/raw/master/fonts/NanumGothic.ttf \
    || echo "Font 다운로드 실패"

# 애플리케이션 복사
COPY . .

EXPOSE 8080

# Health Check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 환경 변수 ARG → ENV 설정
ARG OPENAI_API_KEY
ARG GEMINI_API_KEY
ARG ELEVENLABS_API_KEY
ARG YOUTUBE_CREDENTIALS
ARG STORAGE_BUCKET
ARG GCP_PROJECT_ID

ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV GEMINI_API_KEY=${GEMINI_API_KEY}
ENV ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}
ENV YOUTUBE_CREDENTIALS=${YOUTUBE_CREDENTIALS}
ENV STORAGE_BUCKET=${STORAGE_BUCKET}
ENV GCP_PROJECT_ID=${GCP_PROJECT_ID}
ENV PYTHONPATH=/app

# Temp/output 디렉토리 생성
RUN mkdir -p /app/temp /app/outputs

# Gunicorn 실행
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8080", "--timeout", "120", "src.main:app"]
