# 1. 베이스 이미지 선택 (파이썬 3.10 버전)
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 필요한 라이브러리 목록 복사 및 설치
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 4. 프로젝트의 모든 코드를 컨테이너 안으로 복사
COPY . .

# 5. 이 컨테이너가 시작될 때 실행할 기본 명령어
# main.py 파일을 실행하도록 설정합니다.
CMD ["python", "main.py"]
