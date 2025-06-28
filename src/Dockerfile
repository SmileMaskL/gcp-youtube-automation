# src/Dockerfile
# Python 3.10 Slim Buster 이미지 사용: 용량이 가볍고, Debian 기반으로 안정적입니다.
FROM python:3.10-slim-buster

# 작업 디렉토리 설정: 컨테이너 내부의 기본 작업 디렉토리로 /app을 사용합니다.
WORKDIR /app

# 시스템 종속성 설치 (ffmpeg 등)
# MoviePy와 같은 비디오/오디오 처리 라이브러리는 ffmpeg에 의존합니다.
# apt-get update: 패키지 목록을 업데이트합니다.
# apt-get install -y ffmpeg: ffmpeg를 자동으로 'yes' 응답과 함께 설치합니다.
# rm -rf /var/lib/apt/lists/*: 설치 후 APT 캐시를 삭제하여 최종 이미지 크기를 줄입니다.
RUN apt-get update && apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Python 환경 변수 설정: Python의 stdout/stderr 버퍼링을 해제하여 로그를 즉시 확인 가능하게 합니다.
# 이는 컨테이너 시작 실패와 같은 상황에서 문제 진단에 매우 중요합니다.
ENV PYTHONUNBUFFERED=1

# Python 종속성 설치
# requirements.txt 파일을 먼저 복사하여 Docker 레이어 캐싱을 효율적으로 활용합니다.
#   (requirements.txt가 변경되지 않으면 이 레이어는 다시 빌드되지 않음)
# pip install --upgrade pip: pip 자체를 최신 버전으로 업그레이드하여 의존성 설치 문제를 줄입니다.
# pip install --no-cache-dir -r requirements.txt:
#   --no-cache-dir: pip 캐시를 사용하지 않아 이미지 크기를 더욱 줄입니다.
#   -r requirements.txt: requirements.txt에 명시된 모든 라이브러리를 설치합니다.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
# 현재 디렉토리(src)의 모든 파일과 폴더를 컨테이너 내부의 작업 디렉토리(/app)로 복사합니다.
# (이는 app.py, video_script_generator.py 등 모든 .py 파일들이 올바른 위치에 복사됨을 의미합니다.)
COPY . .

# Flask 애플리케이션 실행 명령어
# Gunicorn (프로덕션용 WSGI 서버)을 사용하여 Flask 애플리케이션을 실행합니다.
# --bind 0.0.0.0:$PORT: Cloud Run은 PORT 환경 변수를 자동으로 주입합니다.
#   컨테이너는 이 환경 변수에 정의된 포트에서 수신 대기해야 합니다.
#   0.0.0.0은 모든 네트워크 인터페이스에서 수신 대기함을 의미하여, 외부에서 접근 가능하게 합니다.
# app:app: 'app' 모듈(즉, app.py 파일) 내에서 'app'이라는 이름의 Flask 애플리케이션 인스턴스를 찾아 실행하라는 의미입니다.
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
