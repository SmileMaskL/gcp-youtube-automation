# Python 3.10 이상의 slim 버전을 사용합니다 (Codespaces 기본 환경과 맞춤)
FROM python:3.10-slim-buster

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 패키지 설치 (MoviePy가 의존하는 ffmpeg 등)
# ffmpeg는 비디오 처리 라이브러리인 moviepy의 필수 의존성입니다.
# libsndfile1은 오디오 파일 처리와 관련될 수 있습니다.
RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사
COPY requirements.txt .

# Python 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 폰트 디렉토리 생성 및 폰트 복사
# GitHub Actions 환경에서 폰트 경로를 정확히 지정해야 합니다.
RUN mkdir -p /app/fonts
COPY fonts/Catfont.ttf /app/fonts/Catfont.ttf

# 애플리케이션 코드 복사
COPY src /app/src
COPY .env /app/.env # .env 파일도 복사 (로컬 테스트용)

# 기본 명령어 (GitHub Actions에서는 재정의될 수 있음)
CMD ["python", "-m", "src.batch_processor"]
