# 이 파일의 다른 리소스들 (예: provider, project 등)은 그대로 유지합니다.

# Cloud Storage 버킷 생성
resource "google_storage_bucket" "youtube_shorts_bucket" {
  # 버킷 이름은 전역적으로 고유해야 합니다.
  # 당신의 GCP 프로젝트 ID를 포함하여 고유하게 만드세요.
  name          = "${var.project_id}_youtube_shorts_temp_files" 
  location      = "US-CENTRAL1" # Cloud Run 리전과 동일하게 설정하는 것이 좋습니다.
  project       = var.project_id
  uniform_bucket_level_access = true # 권한 관리를 간소화합니다.

  # 비용 절감을 위한 라이프사이클 관리: 30일 후 임시 파일 자동 삭제
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30 # 생성 후 30일이 지난 객체 삭제
      # prefix = "temp_uploads/" # 특정 접두사를 가진 파일에만 적용할 수도 있습니다.
    }
  }

  # 버킷에 대한 접근 제어
  # Cloud Run 서비스 계정이 이 버킷에 쓰기/읽기/삭제 권한이 있어야 합니다.
  # (이 부분은 IAM Policy binding으로 별도 관리되거나,
  # Cloud Run 서비스 계정에 'Cloud Storage 객체 관리자' 역할을 부여해야 합니다.)
}

# (선택 사항) Cloud Run 서비스 계정에 스토리지 권한 부여
# 이 부분은 deploy-and-run.yml에서 서비스 계정을 지정하므로
# 해당 서비스 계정에 직접 IAM 역할을 부여하는 것이 더 일반적입니다.
/*
resource "google_storage_bucket_iam_member" "bucket_iam_member" {
  bucket = google_storage_bucket.youtube_shorts_bucket.name
  role   = "roles/storage.objectAdmin" # Cloud Storage 객체 관리자 역할
  member = "serviceAccount:94662874801-compute@developer.gserviceaccount.com" # 당신의 Cloud Run 서비스 계정
}
*/
