# src/Dockerfile
# 최신 Debian 기반으로 변경
FROM python:3.11-slim-bullseye # ✅ 이대로 유지 (us-central1과는 직접 관련 없지만 최신 버전 권장)

WORKDIR /app

# 파이썬 종속성 복사
COPY requirements.txt .

# apt update 후 gcc 설치 (pandas, numpy 등 빌드 필요시)
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# 파이썬 종속성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스 복사
COPY . .

# 앱 실행
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"] 
# ✅ FastAPI 실행을 위해 이 명령어로 변경 (app.py가 FastAPI 앱인 경우)
