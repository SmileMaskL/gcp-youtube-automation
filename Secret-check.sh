#!/bin/bash

# 환경 변수 설정 (테스트용 - 실제로는 GitHub Actions에서 설정됨)
export GCP_AUDIENCE="//iam.googleapis.com/projects/94662874801/locations/global/workloadIdentityPools/github-pool-v2/providers/github-provider"
export GCP_SERVICE_ACCOUNT="your-service-account@youtube-fully-automated.iam.gserviceaccount.com"
export GCP_WORKLOAD_IDENTITY_PROVIDER=$GCP_AUDIENCE
export PROJECT_ID="youtube-fully-automated"

# 모든 시크릿 기본 검증
echo "🔐 GCP_AUDIENCE: $GCP_AUDIENCE"
echo "🔑 GCP_SERVICE_ACCOUNT: $GCP_SERVICE_ACCOUNT"
echo "🌐 GCP_WORKLOAD_IDENTITY_PROVIDER: $GCP_WORKLOAD_IDENTITY_PROVIDER"

# 핵심 검증 1: Audience 형식
if [[ $GCP_WORKLOAD_IDENTITY_PROVIDER != *"iam.googleapis.com"* ]]; then
  echo "❌ 치명적 오류: audience 형식이 잘못되었습니다!"
  echo "현재 값: $GCP_WORKLOAD_IDENTITY_PROVIDER"
  echo "올바른 형식: //iam.googleapis.com/projects/[번호]/locations/global/workloadIdentityPools/[풀이름]/providers/[프로바이더]"
  exit 1
else
  echo "✅ Audience 형식 정상!"
fi

# 핵심 검증 2: 서비스 계정 형식
if [[ $GCP_SERVICE_ACCOUNT != *"@$PROJECT_ID.iam.gserviceaccount.com"* ]]; then
  echo "❌ 치명적 오류: 서비스 계정 형식 오류!"
  echo "현재 값: $GCP_SERVICE_ACCOUNT"
  echo "올바른 형식: [계정명]@$PROJECT_ID.iam.gserviceaccount.com"
  exit 1
else
  echo "✅ 서비스 계정 형식 정상!"
fi

# 핵심 검증 3: 필수 키 존재 여부
required_secrets=(
  "OPENAI_API_KEYS"
  "PEXELS_API_KEY"
  "YOUTUBE_CLIENT_ID"
  "YOUTUBE_CLIENT_SECRET"
  "YOUTUBE_REFRESH_TOKEN"
)

for secret in "${required_secrets[@]}"; do
  if [ -z "${!secret}" ]; then
    echo "❌ 치명적 오류: $secret 이(가) 설정되지 않았습니다!"
    exit 1
  else
    echo "✅ $secret 설정됨"
  fi
done

echo "🎉 모든 시크릿 검증 통과!"
