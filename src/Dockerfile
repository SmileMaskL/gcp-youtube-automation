# src/Dockerfile
# 최신 Debian 기반으로 변경
FROM python:3.11-slim-bookworm

WORKDIR /app

# 파이썬 종속성 복사
COPY src/requirements.txt .

# apt update 후 gcc 설치 (pandas, numpy 등 빌드 필요시)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    pip install --no-cache-dir -r requirements.txt

COPY src/ .

# 앱 실행
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
