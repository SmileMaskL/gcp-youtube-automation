# ✅ 파이썬 3.10 슬림 이미지를 사용합니다
FROM python:3.10-slim

# ✅ 필요한 시스템 패키지들을 설치합니다
RUN apt-get update && \
    apt-get install -y ffmpeg curl python3-dev libsm6 libxext6 libxrender1 && \
    apt-get clean

# ✅ 작업 폴더를 만듭니다
WORKDIR /app

# ✅ 모든 파일을 복사합니다
COPY . .

# ✅ 파이썬 패키지들을 설치합니다
RUN pip install --upgrade pip && \
    pip install moviepy==1.0.3 && \
    pip install --no-cache-dir youtube-upload

# ✅ 실행 명령어를 설정합니다
CMD ["python", "src/content_generator.py"]
