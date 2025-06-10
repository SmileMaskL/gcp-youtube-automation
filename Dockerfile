# 1. 베이스 이미지 선택 (파이썬 3.10)
FROM python:3.10-slim

# 2. 시스템 업데이트 및 ffmpeg 설치
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. 폰트와 로그를 위한 폴더 생성
RUN mkdir -p /app/fonts /app/logs

# 5. 로컬의 폰트 파일을 컨테이너로 복사
# 중요: 로컬 프로젝트에 fonts 폴더를 만들고 그 안에 Catfont.ttf 파일을 넣어주세요.
COPY fonts/ /app/fonts/

# 6. 파이썬 라이브러리 설치
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 7. 프로젝트의 모든 코드를 컨테이너 안으로 복사
COPY . .

# 8. 컨테이너 시작 시 실행할 기본 명령어
CMD ["python", "main.py"]
