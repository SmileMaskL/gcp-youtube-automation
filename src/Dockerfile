# src/Dockerfile
# Python 3.11 Slim 이미지 사용 (가장 안정적이고 경량)
FROM python:3.11-slim-buster

# ffmpeg 및 moviepy 사용을 위한 추가 시스템 라이브러리 설치
# Cloud Run 환경에서 필요한 패키지들을 설치합니다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libjpeg-dev \
    zlib1g-dev \
    # 필요한 경우 ImageMagick 설치 (moviepy에 도움이 될 수 있음)
    # imagemagick \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 파일 복사 (캐싱 활용을 위해 먼저 복사)
COPY requirements.txt .

# Python 종속성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
# .dockerignore 파일을 사용하여 불필요한 파일은 복사하지 않도록 합니다.
# src/ 폴더 안에 app.py가 있다면, /app/src/app.py 경로가 됩니다.
COPY . /app 

# ⭐ 추가: Pexels 이미지 실패 시 사용할 기본 이미지 복사
#    이 파일은 src/app.py에서 /app/default_image.jpg 경로로 사용됩니다.
#    따라서 'src' 폴더 안에 'default_image.jpg' 파일을 넣어주세요.
COPY src/default_image.jpg /app/default_image.jpg 

# Cloud Run이 Flask 애플리케이션을 실행할 포트 설정 (Cloud Run에 의해 자동 주입됨)
ENV PORT 8080

# Gunicorn을 사용하여 Flask 애플리케이션 실행
# --bind 0.0.0.0:$PORT : 모든 네트워크 인터페이스에서 PORT 환경 변수에 지정된 포트를 리스닝합니다.
# --workers 1 : 단일 워커 (Cloud Run 인스턴스당 하나의 컨테이너 프로세스)
# --timeout 0 : 요청 타임아웃을 무한대로 설정 (장시간 비동기 작업에 유용)
# --graceful-timeout 30 : 앱이 완전히 로드될 때까지 30초 대기. 이 시간 내에 시작되지 않으면 종료.
# 'src.app:app' : src 폴더 안의 app.py 파일 내의 'app' Flask 인스턴스를 찾아 실행합니다.
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 0 --graceful-timeout 30 src.app:app
