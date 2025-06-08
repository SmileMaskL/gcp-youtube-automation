#!/bin/bash

echo "🔐 GCP_AUDIENCE: $GCP_AUDIENCE"
echo "🔑 GCP_SERVICE_ACCOUNT: $GCP_SERVICE_ACCOUNT"
echo "🌐 WORKLOAD_IDENTITY_PROVIDER: $WORKLOAD_IDENTITY_PROVIDER"

# 추가된 검증
echo "🔍 OPENAI_API_KEYS: ${OPENAI_API_KEYS:0:4}...${OPENAI_API_KEYS: -4}"  # 일부만 표시
echo "📷 PEXELS_API_KEY: ${PEXELS_API_KEY:0:4}...${PEXELS_API_KEY: -4}"
# ... [다른 키들] ...

# GCP_AUDIENCE 검증
if [[ -z "$GCP_AUDIENCE" || ! "$GCP_AUDIENCE" == *"iam.googleapis.com"* ]]; then
  echo "❌ GCP_AUDIENCE 오류: GCP 콘솔의 '대상자(audience)' 값과 비교하세요!"
else
  echo "✅ GCP_AUDIENCE 정상!"
fi

# 서비스 계정 형식 검증
if [[ ! "$GCP_SERVICE_ACCOUNT" =~ @.*\.iam\.gserviceaccount\.com$ ]]; then
  echo "❌ GCP_SERVICE_ACCOUNT 오류: 'service-account-name@project-id.iam.gserviceaccount.com' 형식이어야 합니다!"
else
  echo "✅ GCP_SERVICE_ACCOUNT 정상!"
fi

# ... [다른 검증] ...
