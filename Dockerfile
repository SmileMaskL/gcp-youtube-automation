FROM python:3.10.13-slim
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 wget curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 한글 폰트 설치
RUN wget -O /usr/share/fonts/NanumGothic.ttf \
    https://github.com/naver/nanumfont/raw/master/fonts/NanumGothic.ttf || \
    echo "Font download failed"

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Health Check 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# 환경 변수 설정을 위한 ARG
ARG OPENAI_API_KEY
ARG GEMINI_API_KEY
ARG ELEVENLABS_API_KEY
ARG YOUTUBE_CREDENTIALS
ARG STORAGE_BUCKET
ARG GCP_PROJECT_ID

# 환경 변수 설정
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV GEMINI_API_KEY=${GEMINI_API_KEY}
ENV ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}
ENV YOUTUBE_CREDENTIALS=${YOUTUBE_CREDENTIALS}
ENV STORAGE_BUCKET=${STORAGE_BUCKET}
ENV GCP_PROJECT_ID=${GCP_PROJECT_ID}
ENV PYTHONPATH=/app
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# 포트 설정 (Cloud Run 표준)
EXPOSE 8080

# 필요한 디렉토리 생성
RUN mkdir -p /app/temp /app/outputs

# 헬스체크
HEALTHCHECK --interval=30s --timeout=30s \
    CMD curl -f http://localhost:8080/health || exit 1

# 애플리케이션 실행
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT}"]
# CMD exec gunicorn --bind :8080 --workers 1 --threads 8 --timeout 3600 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100 main:app
# CMD ["python", "-m", "src.main"]
