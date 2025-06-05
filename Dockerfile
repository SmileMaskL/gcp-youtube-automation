FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치: ffmpeg, libsm6, libxext6, fontconfig (폰트 사용 위함)
# apt-get update 먼저 실행 후, 필요한 패키지 설치
# Noto Sans CJK KR 폰트 설치 (한글 깨짐 방지 및 고양이체.ttf 사용 전 대비)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    fontconfig \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 요구사항 파일 복사 및 파이썬 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 모든 소스 코드 복사
COPY . .

# 폰트 캐시 재생성 (MoviePy에서 폰트 사용 시 필요)
RUN fc-cache -fv

# Gunicorn으로 Flask 애플리케이션 실행
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app", "--timeout", "300"]
