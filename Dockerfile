# ✅ 1. 파이썬 3.10 슬림 이미지
FROM python:3.10-slim

# ✅ 2. 필수 패키지 설치 (ffmpeg 포함)
RUN apt-get update && apt-get install -y ffmpeg curl && apt-get clean

# ✅ 3. 작업 디렉토리 설정
WORKDIR /app

# ✅ 4. 모든 파일 복사
COPY . .

# ✅ 5. 파이썬 패키지 설치
RUN pip install --upgrade pip && pip install -r requirements.txt

# ✅ 6. 메인 실행 파일 지정
CMD ["python", "src/content_generator.py"]
