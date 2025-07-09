FROM python:3.11-slim-buster

# 필수 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libsm6 \
        libxext6 \
        libglib2.0-0 \
        libimage-exiftool-perl \
        wget && \
    pip install moviepy requests pillow && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# --- 여기를 수정합니다. ---
# CMD를 쉘 형식으로 변경하여 ${PORT} 환경 변수가 올바르게 확장되도록 합니다.
# 쉘 형식은 CMD "command arg1 arg2" 와 같이 문자열로 작성됩니다.
CMD gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:${PORT}
