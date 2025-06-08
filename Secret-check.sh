#!/bin/bash

# GitHub Secrets 값 출력 (테스트용)
echo "🔐 GCP_AUDIENCE: $GCP_AUDIENCE"
echo "🔑 GCP_SERVICE_ACCOUNT: $GCP_SERVICE_ACCOUNT"
echo "🌐 WORKLOAD_IDENTITY_PROVIDER: $WORKLOAD_IDENTITY_PROVIDER"

# 값 검증 테스트
if [[ -z "$GCP_AUDIENCE" || ! "$GCP_AUDIENCE" == *"iam.googleapis.com"* ]]; then
  echo "❌ GCP_AUDIENCE 오류: GCP 콘솔의 '대상자(audience)' 값과 비교하세요!"
else
  echo "✅ GCP_AUDIENCE 정상!"
fi
