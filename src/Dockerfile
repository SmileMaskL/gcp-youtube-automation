# 파이썬 3.11 버전의 경량 이미지를 사용합니다.
# FROM python:3.11-slim-buster  <-- 이 줄 대신
FROM python:3.11-slim-bullseye # 또는 python:3.11-slim-bookworm

# 작업 디렉토리를 /app으로 설정합니다.
WORKDIR /app

# 현재 디렉토리 (즉, src 디렉토리)의 모든 파일과 폴더를
# 컨테이너의 /app 디렉토리로 복사합니다.
COPY . /app

# 파이썬 종속성 설치 (requirements.txt가 /app에 있으므로 정상 작동)
RUN pip install --no-cache-dir -r requirements.txt

# apt-get update 및 gcc 설치 (최신 이미지에서는 잘 작동할 것입니다)
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# 애플리케이션 실행 명령어를 설정합니다.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
