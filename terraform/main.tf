terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = ">= 5.0.0"
    }
  }

  # ⭐ 이 부분을 확인하여 bucket 이름이 PROJECT_ID-tf-state와 일치하는지 확인! ⭐
  backend "gcs" {
    bucket = "youtube-fully-automated-tf-state" # ⬅️ 이 부분을 수정 (또는 확인)
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
}

resource "google_project_service" "project_services" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "cloudscheduler.googleapis.com",
    "pubsub.googleapis.com", # Cloud Scheduler -> Cloud Run 연동에 필요
    "logging.googleapis.com", # 로그 확인용
  ])
  project = var.project_id
  service = each.key
  disable_on_destroy = false
}

resource "google_storage_bucket" "youtube_shorts_temp_files" {
  name          = "${var.project_id}_youtube_shorts_temp_files"
  location      = "US" # Cloud Run 리전과 가깝게 설정 (예: us-central1)
  project       = var.project_id
  force_destroy = true # 버킷 삭제 시 내용물도 강제 삭제

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 7 # 7일 이상 된 객체 자동 삭제
    }
  }

  depends_on = [
    google_project_service.project_services["storage.googleapis.com"]
  ]
}

# Terraform State 저장용 버킷
resource "google_storage_bucket" "terraform_state_bucket" {
  name     = "${var.project_id}-tf-state" # ⭐ Terraform State 버킷 이름 (PROJECT_ID-tf-state) ⭐
  location = "US" # Terraform State 버킷은 일반적으로 멀티 리전에 두어도 무방
  project  = var.project_id

  uniform_bucket_level_access = true # 권한 관리를 간소화

  versioning {
    enabled = true # Terraform State 버전 관리
  }

  lifecycle {
    prevent_destroy = true # 실수로 버킷이 삭제되는 것을 방지
  }

  depends_on = [
    google_project_service.project_services["storage.googleapis.com"]
  ]
}

resource "google_project_iam_member" "cloud_run_invoker_for_scheduler" {
  project = var.project_id
  role    = "roles/run.invoker" # Cloud Scheduler가 Cloud Run을 호출할 권한
  member  = "serviceAccount:${var.compute_service_account_email}"
  # 참고: Default compute service account (94662874801-compute@developer.gserviceaccount.com)
}

# Cloud Scheduler Pub/Sub Topic 생성
resource "google_project_iam_member" "cloud_scheduler_sa_pubsub_publisher" {
  project = var.project_id
  role    = "roles/editor" # roles/editor는 pubsub.publisher 권한을 포함
  member  = "serviceAccount:service-${var.project_number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
}
