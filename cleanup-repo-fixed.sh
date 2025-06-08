!/bin/bash
MAX_SIZE_MB=3000  # GCP 무료 한도
REPO_NAME="youtube-auto-upload"

# 현재 저장소 크기 체크 (MB 단위)
CURRENT_SIZE_BYTES=$(gcloud artifacts repositories describe $REPO_NAME \
  --location=us-central1 --format="value(sizeBytes)")
CURRENT_SIZE_MB=$((CURRENT_SIZE_BYTES / 1000000))

# 삭제 필요한 용량 계산
if (( CURRENT_SIZE_MB > MAX_SIZE_MB )); then
  DELETE_SIZE=$((CURRENT_SIZE_MB - MAX_SIZE_MB))
  # 이미지 1개당 200MB 가정 → 삭제 개수 계산
  DELETE_COUNT=$(( (DELETE_SIZE + 199) / 200 ))

  echo "🧹 저장소 청소: ${CURRENT_SIZE_MB}MB → ${DELETE_COUNT}개 이미지 삭제"
  
  # 가장 오래된 이미지 삭제
  gcloud artifacts docker images list us-central1-docker.pkg.dev/youtube-fully-automated/$REPO_NAME \
    --sort-by=UPDATE_TIME --limit=$DELETE_COUNT --format="value(digest)" | while read DIGEST; do
    gcloud artifacts docker images delete us-central1-docker.pkg.dev/youtube-fully-automated/$REPO_NAME@$DIGEST --delete-tags --quiet
  done
fi
