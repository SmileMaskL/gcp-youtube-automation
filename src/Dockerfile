# 멀티스테이지 빌드
FROM python:3.11-bookworm as builder

# 1. 빌드 종속성
RUN apt-get update && apt-get install -y \
    build-essential wget perl

# 2. ExifTool 설치 (버전 관리)
ARG EXIFTOOL_VERSION=12.87
RUN wget "https://exiftool.org/Image-ExifTool-${EXIFTOOL_VERSION}.tar.gz" -O /tmp/Image-ExifTool.tar.gz && \
    mkdir -p /tmp/exiftool_build && \
    tar -xzf /tmp/Image-ExifTool.tar.gz -C /tmp/exiftool_build && \
    cd "/tmp/exiftool_build/Image-ExifTool-${EXIFTOOL_VERSION}" && \
    perl Makefile.PL && \
    make && make install

# 최종 이미지
FROM python:3.11-slim-bookworm

# 3. 런타임 종속성
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 libglib2.0-0 libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

# 4. ExifTool 복사
COPY --from=builder /usr/local/bin/exiftool /usr/local/bin/
COPY --from=builder /usr/local/share/man/man1/exiftool.1 /usr/local/share/man/man1/

# 5. GCP 인증 설정
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/gcp_credentials.json

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "300"]
