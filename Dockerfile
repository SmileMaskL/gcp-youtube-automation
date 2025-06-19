FROM python:3.10-slim-buster
WORKDIR /app

RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/fonts
COPY fonts/Catfont.ttf /app/fonts/Catfont.ttf

COPY src /app/src

CMD ["python", "-m", "src.batch_processor"]
