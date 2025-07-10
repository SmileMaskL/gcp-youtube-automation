#!/bin/bash
echo "🔧 테스트 시작..."
export PYTHONPATH="/workspaces/gcp-youtube-automation/src:$PYTHONPATH"
python3 -m pytest tests/
