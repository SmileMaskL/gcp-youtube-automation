# 핵심 라이브러리
Flask==3.0.2
flask-pymongo==3.0.1 # MongoDB와 Flask 연동 (사용 여부 확인 필요, 없으면 삭제 가능)

google-cloud-secret-manager==2.24.0
openai==1.35.13 # GPT-4o 사용
google-cloud-storage==2.16.0
google-generativeai==0.8.5 # Google Gemini 사용
elevenlabs==1.2.0

# Google 관련
google-auth==2.29.0
google-auth-oauthlib==1.2.0
google-api-python-client==2.136.0 # YouTube Data API 사용

# Cloud Functions
functions-framework==3.* # Cloud Function 진입점

# 미디어 처리 (FFmpeg 필요)
Pillow==10.3.0
moviepy==1.0.3
imageio-ffmpeg==0.4.9

# 기타 유틸리티
newsapi-python==0.2.7
requests==2.32.3
beautifulsoup4==4.12.3 # 웹 스크래핑 (사용 여부 확인 필요, 없으면 삭제 가능)
python-dotenv==1.0.1 # 로컬 개발용 (Cloud Function에는 필요 없음, 삭제 가능)
python-json-logger==2.0.7 # 로깅 (사용 여부 확인 필요)
setuptools==68.0.0

# 추가 설치
# ⭐ 수정 부분: Pexels API는 requests로 직접 호출하거나, 'pexels_api'와 같은
# 공식/안정적인 라이브러리를 사용하세요. 'Pexels==0.0.11'은 권장하지 않습니다.
# 여기서는 직접 requests를 사용한다고 가정하고 삭제합니다.
# numpy, pandas는 데이터 분석 라이브러리. 동영상/AI 콘텐츠 생성에 직접 필요 없을 수 있음.
# 필요 없으면 삭제하여 배포 크기 줄이기.
numpy==1.26.4
pandas==2.2.2
# ⭐ 수정 부분: httplib2는 대부분 최신 Google 라이브러리에 내장되므로 제거합니다.
# pydub는 오디오 처리 라이브러리 (FFmpeg 필요).
pydub==0.25.1
