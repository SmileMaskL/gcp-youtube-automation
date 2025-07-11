FROM python:3.11-slim-bookworm

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 libglib2.0-0 libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정 (변경)
# ★ /app/src에서 /app으로 변경 ★
WORKDIR /app
COPY . .

# Python 경로 설정
ENV PYTHONPATH="/app"

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 실행 명령어 (변경)
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8080"]
