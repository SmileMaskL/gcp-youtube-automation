FROM python:3.10-slim-buster

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libsndfile1 \
    wget && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/fonts
COPY fonts/Catfont.ttf /app/fonts/

COPY src /app/src

# Cloud Run Jobs은 포트 리스닝이 필요 없음
CMD ["python", "-m", "src.batch_processor"]
