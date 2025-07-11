# src/Dockerfile

# --- 빌드 스테이지 ---
FROM python:3.11-bookworm AS builder
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# --- 런타임 스테이지 ---
FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsm6 libxext6 libglib2.0-0 libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/src
COPY requirements.txt ../
RUN pip install --no-cache-dir -r ../requirements.txt
COPY . .

# ★ 핵심 설정: Python이 /app/src를 모듈로 인식하도록 ★
ENV PYTHONPATH="/app"

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "300"]
