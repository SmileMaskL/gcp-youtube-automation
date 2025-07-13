# 파이썬 3.11 버전의 경량 이미지를 사용합니다.
FROM python:3.11-slim-buster

# 작업 디렉토리를 /app으로 설정합니다.
# 이제 /app이 여러분의 src 디렉토리의 내용물이 됩니다.
WORKDIR /app

# 현재 디렉토리 (즉, src 디렉토리)의 모든 파일과 폴더를
# 컨테이너의 /app 디렉토리로 복사합니다.
# 이렇게 하면 app.py, video_engine.py 등이 모두 /app 안에 들어가게 됩니다.
COPY . /app

# 파이썬 종속성 설치 (requirements.txt가 /app에 있으므로 정상 작동)
RUN sed -i 's|http://deb.debian.org/debian|http://deb.debian.org/debian-security|g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends gcc

# 애플리케이션 실행 명령어를 설정합니다.
# app.py가 /app/app.py에 있으므로, 'app:app'이 맞습니다.
# 만약 app.py가 /app/src/app.py에 있다면 'src.app:app'이어야 합니다.
# 현재 구조상 src/app.py는 Dockerfile 관점에서 보면 ./app.py로 복사되므로, 'app:app'을 유지합니다.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
