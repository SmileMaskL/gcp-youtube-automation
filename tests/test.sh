#!/bin/bash
echo "✅ 계층적 테스트 시작..."
export PYTHONPATH="/workspaces/gcp-youtube-automation/src:$PYTHONPATH"

# 단위 테스트와 통합 테스트 분리 실행
pytest tests/unit --cov=src --cov-report=html
pytest tests/integration --cov=src --cov-report=html

