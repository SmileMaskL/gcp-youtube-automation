# Python 3.11 Slim 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (필요시)
# apt-get update && apt-get install -y --no-install-recommends \
#   ffmpeg \ # 비디오 처리 관련 라이브러리가 필요하다면 주석 해제
#   && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 설정 (Cloud Run에서 PORT 환경 변수로 자동 주입)
# ENV PORT 8080 # Cloud Run이 자동으로 설정하므로 명시적으로 지정할 필요 없음

# Gunicorn을 사용하여 Flask 애플리케이션 실행
# Gunicorn은 app.py 파일 내의 'app'이라는 Flask 인스턴스를 찾아서 실행합니다.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 --chdir /app app:app
