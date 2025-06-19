# Python 3.10 이상의 slim 버전을 사용합니다 (Codespaces 기본 환경과 맞춤)
FROM python:3.10-slim-buster

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 패키지 설치 (MoviePy가 의존하는 ffmpeg 등)
RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사
COPY requirements.txt .

# Python 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 폰트 디렉토리 생성 및 폰트 복사
RUN mkdir -p /app/fonts
COPY fonts/Catfont.ttf /app/fonts/Catfont.ttf

# 애플리케이션 코드 복사
COPY src /app/src

# .env 파일 복사 (로컬 테스트용) - 주석 처리: GitHub Actions에서는 불필요
# COPY .env /app/.env

# 기본 명령어 (GitHub Actions에서는 재정의될 수 있음)
CMD ["python", "-m", "src.batch_processor"]
