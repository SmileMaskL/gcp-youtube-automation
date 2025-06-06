FROM python:3.10-slim

# 필수 도구 설치
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 종속성 먼저 설치 (캐시 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# 환경 변수 설정
ARG YOUTUBE_CLIENT_ID
ARG YOUTUBE_CLIENT_SECRET
ARG YOUTUBE_REFRESH_TOKEN
ARG OPENAI_API_KEYS
ARG GCP_SERVICE_ACCOUNT_KEY

ENV YOUTUBE_CLIENT_ID=$YOUTUBE_CLIENT_ID
ENV YOUTUBE_CLIENT_SECRET=$YOUTUBE_CLIENT_SECRET
ENV YOUTUBE_REFRESH_TOKEN=$YOUTUBE_REFRESH_TOKEN
ENV OPENAI_API_KEYS=$OPENAI_API_KEYS
ENV GCP_SERVICE_ACCOUNT_KEY=$GCP_SERVICE_ACCOUNT_KEY
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# 소스 코드 복사
COPY . .

# 포트 설정
EXPOSE 8080

# Artifact Registry 인증 설정
RUN echo "$GCP_SERVICE_ACCOUNT_KEY" > /app/gcp_key.json
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/gcp_key.json

# 실행 명령
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]
