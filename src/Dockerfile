# src/Dockerfile
# Python 3.11 Slim 이미지 사용 (가장 안정적이고 경량)
FROM python:3.11-slim-buster

# apt-get 업데이트 및 ffmpeg 설치
# ffmpeg은 MoviePy가 비디오 처리를 위해 사용하는 필수 라이브러리입니다.
# --no-install-recommends 옵션으로 불필요한 패키지 설치를 줄여 이미지 크기를 최적화합니다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 애플리케이션 종속성 복사
COPY requirements.txt .

# Python 종속성 설치
# --no-cache-dir: 캐시 디렉토리를 사용하지 않아 이미지 크기 증가 방지
# --upgrade pip: pip 최신 버전 유지
RUN pip install --no-cache-dir --upgrade pip
# --- ⭐ 추가: pip 설치 디버깅을 위한 --verbose 옵션 ⭐ ---
# 이 옵션은 설치 과정 중 발생하는 상세한 로그를 보여주어 에러 원인 파악에 도움을 줍니다.
RUN pip install --no-cache-dir --verbose -r requirements.txt # <--- 이 라인이 수정되었습니다!

# --- ⭐ 추가: 현재 작업 디렉토리 내용 확인 (디버깅용) ⭐ ---
# 이 명령은 빌드 로그에 현재 /app 디렉토리의 파일 목록을 출력하여
# COPY . . 이 제대로 동작했는지, 파일이 누락되지 않았는지 확인할 수 있습니다.
RUN ls -la /app # <--- 이 라인이 추가되었습니다!

# 애플리케이션 코드 복사
# .gcloudignore 파일이 있다면, 해당 파일에 명시된 내용은 복사되지 않습니다.
# (src 폴더를 통째로 올리므로, 이 단계에서 불필요한 .git 같은 폴더는 제외됩니다)
COPY . .

# ⭐ 수정: Pexels 이미지 실패 시 사용할 기본 이미지 복사
#   이 파일은 src/app.py에서 /app/default_image.jpg 경로로 사용됩니다.
#   'src' 폴더 자체가 빌드 컨텍스트이므로 'src/' 접두사는 제거합니다.
COPY default_image.jpg /app/default_image.jpg

# Cloud Run은 PORT 환경 변수로 포트를 지정하므로, 이 변수를 따르도록 Flask 앱 설정
ENV PORT 8080

# 컨테이너가 시작될 때 실행할 명령어
# ⭐️⭐️⭐️ gunicorn을 사용해서 src.app:app을 실행합니다! ⭐️⭐️⭐️
# 프로젝트 구조에 따라 src.app:app이 올바른 경로인지 확인해주세요. (현재 구조로는 맞습니다)
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 0 --graceful-timeout 30 src.app:app
