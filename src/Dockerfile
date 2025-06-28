# src/Dockerfile
FROM python:3.10-slim-buster

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Flask 애플리케이션 실행 명령어
# Gunicorn을 사용하여 app.py 파일의 'app' 객체를 실행합니다.
# Cloud Run은 PORT 환경 변수를 자동으로 주입하므로, $PORT를 사용합니다.
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
