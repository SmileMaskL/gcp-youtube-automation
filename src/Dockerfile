# src/Dockerfile
# Python 3.10 Slim 이미지 사용 (경량화)
FROM python:3.10-slim-buster

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 종속성 설치 (ffmpeg 등)
# MoviePy가 비디오 처리를 위해 ffmpeg에 의존합니다.
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# 파이썬 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Flask 애플리케이션 실행 명령어
# Cloud Run은 PORT 환경 변수를 자동으로 주입합니다.
# 0.0.0.0으로 바인딩해야 Cloud Run에서 접근 가능합니다.
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]
