# 파이썬 3.9 기반
FROM python:3.10-slim

# FFmpeg 설치 (가장 중요한 단계!)
RUN apt-get update && apt-get install -y ffmpeg

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 파일 복사
COPY . /app

# 패키지 설치
RUN pip install --upgrade pip && pip install -r requirements.txt

# 앱 실행
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
CMD ["python", "src/content_generator.py"]
