# src/Dockerfile
# Python 3.11 Slim 이미지 사용 (가장 안정적이고 경량)
FROM python:3.11-slim-buster

# apt-get 업데이트 및 ffmpeg 설치
# ffmpeg은 MoviePy가 비디오 처리를 위해 사용하는 필수 라이브러리입니다.
# --no-install-recommends 옵션으로 불필요한 패키지 설치를 줄여 이미지 크기를 최적화합니다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    # 필요한 경우 다른 시스템 라이브러리 추가
    # 예를 들어, 이미지 처리 라이브러리 (libsm6, libxext6)
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 애플리케이션 종속성 복사
COPY requirements.txt .

# Python 종속성 설치
# --no-cache-dir: 캐시 디렉토리를 사용하지 않아 이미지 크기 증가 방지
# --upgrade pip: pip 최신 버전 유지
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Cloud Run은 PORT 환경 변수로 포트를 지정하므로, 이 변수를 따르도록 Flask 앱 설정
ENV PORT 8080

# 컨테이너가 시작될 때 실행할 명령어
# gunicorn 대신 Flask 개발 서버를 직접 사용해도 됩니다.
# 하지만 프로덕션 환경에서는 gunicorn이나 uWSGI와 같은 WSGI 서버를 권장합니다.
# gunicorn을 사용하지 않는다면 main.py의 if __name__ == '__main__': 부분을 사용합니다.
CMD ["python", "app.py"]
