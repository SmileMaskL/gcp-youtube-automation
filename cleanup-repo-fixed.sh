#!/bin/bash

# 설정값
MAX_SIZE_MB=3000  # GCP 무료 한도 (3GB)
REPO_NAME="youtube-auto-upload"
PROJECT_ID="youtube-fully-automated"
LOCATION="us-central1"
IMAGE_SIZE_ESTIMATE=200  # 이미지 1개당 예상 크기 (MB)

# 현재 저장소 크기 체크 (MB 단위)
CURRENT_SIZE_BYTES=$(gcloud artifacts repositories describe $REPO_NAME \
  --location=$LOCATION --project=$PROJECT_ID --format="value(sizeBytes)")
CURRENT_SIZE_MB=$(echo "$CURRENT_SIZE_BYTES / 1000000" | bc)

echo "🔍 현재 저장소 크기: ${CURRENT_SIZE_MB}MB (최대 허용 크기: ${MAX_SIZE_MB}MB)"

# 삭제 필요한 용량 계산
if (( $(echo "$CURRENT_SIZE_MB > $MAX_SIZE_MB" | bc -l) )); then
  DELETE_SIZE=$(echo "$CURRENT_SIZE_MB - $MAX_SIZE_MB" | bc)
  DELETE_COUNT=$(echo "($DELETE_SIZE + $IMAGE_SIZE_ESTIMATE - 1) / $IMAGE_SIZE_ESTIMATE" | bc)

  echo "🧹 저장소 청소 필요: ${DELETE_COUNT}개 이미지 삭제 (${DELETE_SIZE}MB 초과)"
  
  # 가장 오래된 이미지 삭제
  gcloud artifacts docker images list $LOCATION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME \
    --project=$PROJECT_ID \
    --sort-by=UPDATE_TIME \
    --limit=$DELETE_COUNT \
    --format="value(digest)" | while read DIGEST; do
    
    echo "🗑️ 삭제 중: $DIGEST"
    gcloud artifacts docker images delete $LOCATION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME@$DIGEST \
      --project=$PROJECT_ID \
      --delete-tags \
      --quiet
  done

  # 삭제 후 크기 재확인
  NEW_SIZE_BYTES=$(gcloud artifacts repositories describe $REPO_NAME \
    --location=$LOCATION --project=$PROJECT_ID --format="value(sizeBytes)")
  NEW_SIZE_MB=$(echo "$NEW_SIZE_BYTES / 1000000" | bc)
  echo "✅ 청소 완료: 새로운 저장소 크기 ${NEW_SIZE_MB}MB"
else
  echo "👍 저장소 크기가 정상 범위 내에 있습니다. 청소가 필요 없습니다."
fi
