# src/Dockerfile

FROM python:3.11-slim-buster

RUN apt-get update && \
    apt-get install -y ffmpeg libimage-exiftool-perl wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8080

CMD ["gunicorn", "--worker-class", "gevent", "--workers", "1", "--timeout", "0", "app:app"]
