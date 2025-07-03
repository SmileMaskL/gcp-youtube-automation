# src/Dockerfile

# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y ffmpeg

# ✅ 작업 디렉토리를 /app으로 설정
WORKDIR /app

# ✅ requirements.txt 복사
COPY requirements.txt ./

# ✅ 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# ✅ 모든 소스 코드 복사
COPY . ./

# 포트 환경 변수
ENV PORT=8080

# ✅ Gunicorn 실행 (src 디렉토리 내부 app.py를 실행)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
