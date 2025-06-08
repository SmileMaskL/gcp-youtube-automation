# Python 3.9 기반 이미지 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 폰트 복사
COPY fonts/Catfont.ttf /usr/share/fonts/truetype/

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 로그 디렉토리 생성
RUN mkdir -p logs

# 환경 변수 설정 (실제 값은 런타임에 주입)
ENV PYTHONUNBUFFERED=1

# 앱 실행
CMD ["python", "app.py"]
