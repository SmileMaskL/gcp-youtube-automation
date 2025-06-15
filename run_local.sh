#!/bin/bash

# 리소스 제한 설정 (Linux/macOS)
ulimit -Sv 6000000  # 6GB 메모리 제한

# 가상 환경 설정
python -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# FFmpeg 설치 확인
ffmpeg -version || echo "FFmpeg 설치 필요"

# 메인 스크립트 실행
python src/main.py

# 임시 파일 정리
rm -rf temp/*
