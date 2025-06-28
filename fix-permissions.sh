#!/bin/bash

# =============================================================================
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# 필수 주의사항: 이 스크립트를 실행하기 전에 반드시 아래 사항을 확인하세요!
# 
# 1. Google Cloud SDK(gcloud)가 설치되어 있어야 합니다
# 2. 실행 전에 'gcloud auth login'으로 인증을 완료해야 합니다
# 3. 프로젝트 ID가 정확한지 확인하세요 (현재 설정: youtube-fully-automated)
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# =============================================================================

# 프로젝트 ID 설정 (youtube-fully-automated로 고정)
GCP_PROJECT_ID="youtube-fully-automated"

# 서비스 계정 이메일 생성 (표준 형식)
SERVICE_ACCOUNT_EMAIL="github-actions-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

echo "============================================================"
echo "🛠  서비스 계정 권한 설정 시작"
echo "📌 프로젝트 ID: ${GCP_PROJECT_ID}"
echo "📧 서비스 계정: ${SERVICE_ACCOUNT_EMAIL}"
echo "============================================================"
echo ""

# 필수 API 활성화 확인
echo "🔌 필수 Google Cloud API 활성화 확인 중..."
gcloud services enable \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com \
  --project="${GCP_PROJECT_ID}"

echo ""
echo "🔑 필수 IAM 권한 추가를 시작합니다..."
echo ""

# IAM 권한 추가 함수 정의
add_iam_binding() {
  local role=$1
  echo "${role} 권한 추가 중..."
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="${role}" \
    --condition=None \
    --quiet >/dev/null || echo "⚠️ ${role} 권한 추가 실패 (이미 존재할 수 있음)"
}

# 1. 서비스 사용 권한
add_iam_binding "roles/serviceusage.serviceUsageConsumer"

# 2. Cloud Run 관리자 권한
add_iam_binding "roles/run.admin"

# 3. Artifact Registry 관리자 권한
add_iam_binding "roles/artifactregistry.admin"

# 4. Cloud Build 편집자 권한
add_iam_binding "roles/cloudbuild.editor"

# 5. Cloud Storage 관리자 권한
add_iam_binding "roles/storage.admin"

# 6. 서비스 계정 토큰 생성자 권한
add_iam_binding "roles/iam.serviceAccountTokenCreator"

# 7. 서비스 계정 사용자 권한
add_iam_binding "roles/iam.serviceAccountUser"

echo ""
echo "✅ 모든 필수 IAM 권한 추가 시도가 완료되었습니다!"
echo "============================================================"
echo "⚠️ 주의: 일부 권한이 이미 존재할 수 있습니다. 실제 적용 여부를 확인하세요."
echo "👉 확인 명령어:"
echo "   gcloud projects get-iam-policy ${GCP_PROJECT_ID} \\"
echo "     --flatten=\"bindings[].members\" \\"
echo "     --format=\"table(bindings.role)\" \\"
echo "     --filter=\"bindings.members:${SERVICE_ACCOUNT_EMAIL}\""
echo "============================================================"
