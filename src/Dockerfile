FROM python:3.11-slim-buster

# 필수 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libimage-exiftool-perl \
        wget && \
        build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 빌드 도구는 런타임에 필요 없으므로 제거 (선택 사항이지만 이미지 크기 최적화에 도움)
RUN apt-get purge -y build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--worker-class", "gevent", "--workers", "1", "--timeout", "0", "app:app"]
