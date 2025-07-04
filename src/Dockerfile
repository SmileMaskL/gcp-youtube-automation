# Dockerfile (프로젝트 루트 디렉토리: ~/gcp-youtube-automation 에 위치)

FROM python:3.11-slim

# ✅ 필수 패키지 설치
RUN apt-get update && \
    apt-get install -y ffmpeg libimage-exiftool-perl wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ✅ 작업 디렉토리 설정
WORKDIR /app

# ✅ requirements.txt 복사 및 설치
# 프로젝트 루트에 있는 src/requirements.txt를 /app/src/requirements.txt로 복사
COPY src/requirements.txt /app/src/requirements.txt
RUN pip install --no-cache-dir -r /app/src/requirements.txt

# ✅ 전체 코드 복사
# 프로젝트 루트의 src 디렉토리 전체를 컨테이너의 /app/src로 복사
COPY src/ /app/src

# ✅ 기본 썸네일 이미지 다운로드 (선택 사항: src 외부나 다른 곳에 두는 것이 더 좋음)
# 만약 default_image.jpg가 src 디렉토리 안에서 사용된다면 src/로 복사
# 여기서는 src/app.py가 이 파일을 필요로 한다고 가정하고 src/ 내부로 다운로드
RUN if [ ! -f "/app/src/default_image.jpg" ]; then \
        wget -O /app/src/default_image.jpg https://via.placeholder.com/1920x1080.png?text=Default+Thumbnail; \
    fi

# ✅ 환경 변수 설정
ENV PORT=8080
ENV MAX_WORKERS=4
# Python이 /app 디렉토리에서 모듈을 찾을 수 있도록 PYTHONPATH 설정
ENV PYTHONPATH=/app:$PYTHONPATH


# ✅ Gunicorn 실행
# Gunicorn은 이제 /app/src/app.py 에서 'app' 객체를 찾을 것입니다.
# Gevent를 사용하려면 `requirements.txt`에 gevent와 greenlet이 설치되어 있어야 합니다.
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "src.app:app"] # 기본 sync worker
CMD ["gunicorn", "--worker-class", "gevent", "--workers", "1", "--timeout", "0", "src.app:app"]
