# src/Dockerfile

FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y ffmpeg libimage-exiftool-perl wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN if [ ! -f "default_image.jpg" ]; then \
        wget -O default_image.jpg https://via.placeholder.com/1920x1080.png?text=Default+Thumbnail; \
    fi

ENV PORT=8080
ENV MAX_WORKERS=4

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
