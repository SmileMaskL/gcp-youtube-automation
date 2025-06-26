# 수정된 파일: terraform/main.tf

variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "gcp_region" {
  description = "The GCP region for Cloud Run."
  type        = string
  default     = "us-central1"
}

variable "cloud_run_service_name" {
  description = "The name for the Cloud Run service."
  type        = string
  default     = "youtube-shorts-automation"
}

variable "gcp_bucket_name" {
  description = "The name for the GCS bucket for temporary files."
  type        = string
}

variable "cloud_run_service_account_email" {
  description = "Email of the service account used by Cloud Run."
  type        = string
}

# --- Cloud Storage 버킷 생성 ---
resource "google_storage_bucket" "youtube_shorts_bucket" {
  name          = var.gcp_bucket_name
  location      = var.gcp_region
  project       = var.project_id
  force_destroy = false # 버킷 내용이 있어도 삭제될 수 있도록 true로 설정할 수 있으나, 일반적으로 false 권장

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 7 # 7일 후 객체 자동 삭제 (임시 파일 관리)
    }
  }

  uniform_bucket_level_access = true # 권장 설정
}

# --- Cloud Run 서비스 계정 권한 부여 (필요한 경우) ---
# Cloud Run은 기본적으로 Compute Engine 기본 서비스 계정을 사용하므로,
# 추가적인 역할 할당이 필요하다면 여기에 정의합니다.
# 이 서비스 계정은 이미 Cloud Storage 및 기타 기본 Google Cloud 서비스에 액세스할 권한을 가지고 있습니다.
# 만약 서비스 계정에 특정 API (예: YouTube Data API, External API 호출)에 대한 추가 권한이 필요하다면 여기에 추가합니다.
resource "google_project_iam_member" "cloud_run_service_account_permissions" {
  project = var.project_id
  role    = "roles/editor" # 배포 및 운영을 위한 포괄적인 역할. 프로덕션 환경에서는 최소 권한 원칙에 따라 더 세분화된 역할 부여 권장
  member  = "serviceAccount:${var.cloud_run_service_account_email}"
}

# --- Cloud Scheduler 작업 생성 ---
# 이 작업은 매일 특정 시간에 Cloud Run 서비스를 트리거합니다.
resource "google_cloud_scheduler_job" "daily_youtube_shorts_upload_job" {
  project  = var.project_id
  region   = var.gcp_region
  name     = "daily-youtube-shorts-upload"
  schedule = "0 10 * * *" # 매일 오전 10시 (UTC) 실행 (자정 KST는 15:00 UTC, 당신이 원하는 시간에 맞게 변경)

  http_target {
    # Cloud Run 서비스의 URL은 배포 후에 결정되므로, 여기에 직접 하드코딩하기 어렵습니다.
    # Cloud Run 서비스 배포 후 수동으로 업데이트하거나, Cloud Build/GitHub Actions에서 동적으로 업데이트해야 합니다.
    # 여기서는 임시 URL을 사용하거나, 배포 후 업데이트를 위한 플레이스홀더로 둡니다.
    # 실제 배포 후 URL은 다음과 같을 것입니다: https://[REGION]-[PROJECT_ID].run.app/[PATH]
    uri = "https://${var.gcp_region}-${var.project_id}.run.app/${var.cloud_run_service_name}/upload-youtube-shorts" # 실제 경로로 변경
    http_method = "POST"
    headers = {
      "Content-Type" = "application/json"
    }
    body = "{}" # Cloud Scheduler는 body가 비어있으면 오류가 나므로 빈 JSON이라도 넣어줍니다.

    # Cloud Run 인증을 위해 OIDC 토큰을 사용합니다.
    oidc_token {
      service_account_email = var.cloud_run_service_account_email
      # Cloud Run 서비스 URL (경로 제외)과 일치해야 합니다.
      audience = "https://${var.gcp_region}-${var.project_id}.run.app/${var.cloud_run_service_name}"
    }
  }
}
