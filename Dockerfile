# Dockerfile
# Python 3.10 slim-buster 이미지 사용 (가벼움)
FROM python:3.10-slim-buster

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 라이브러리 설치 (FFmpeg 및 이미지/오디오 처리에 필요한 라이브러리)
# libsm6, libxext6: moviepy 같은 라이브러리에서 이미지 처리를 위해 필요
# libsndfile1: 오디오 파일 처리에 필요
RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# Python 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 폰트 디렉토리 생성 및 폰트 복사
# 고양이체 폰트 (Catfont.ttf)를 /app/fonts/ 에 복사
RUN mkdir -p /app/fonts
COPY fonts/Catfont.ttf /app/fonts/Catfont.ttf

# 소스 코드 복사
# src 디렉토리의 모든 내용을 /app/src로 복사
COPY src /app/src

# 작업 실행 명령어 설정
# Cloud Run Job은 이 명령어를 실행하고, 작업이 완료되면 컨테이너가 종료됩니다.
# FastAPI 서버를 띄우는 것이 아니므로, 포트 리스닝이 필요 없습니다.
CMD ["python", "-m", "src.batch_processor"]
