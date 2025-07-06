FROM python:3.11-slim-buster

# 필수 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libimage-exiftool-perl \
        wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--worker-class", "gevent", "--workers", "1", "--timeout", "0", "app:app"]
