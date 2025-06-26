terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast3"
}

variable "service_name" {
  description = "Service name"
  type        = string
  default     = "gcp-youtube-automation"
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "youtube.googleapis.com",
    "cloudscheduler.googleapis.com"
  ])
  
  project = var.project_id
  service = each.key
  
  disable_dependent_services = true
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "Cloud Run Service Account for ${var.service_name}"
  description  = "Service account for YouTube automation Cloud Run service"
}

# IAM roles for Service Account
resource "google_project_iam_member" "cloud_run_sa_roles" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/storage.admin",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Storage bucket for video files
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
# Secret Manager secrets
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "youtube_client_secrets" {
  secret_id = "youtube-client-secrets"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "elevenlabs_api_key" {
  secret_id = "elevenlabs-api-key"
  
  replication {
    auto {}
  }
}

# Cloud Run service
resource "google_cloud_run_v2_service" "youtube_automation" {
  name     = var.service_name
  location = var.region
  
  depends_on = [google_project_service.required_apis]
  
  template {
    service_account = google_service_account.cloud_run_sa.email
    
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
    
    containers {
      image = "gcr.io/${var.project_id}/${var.service_name}:latest"
      
      ports {
        container_port = 8080
      }
      
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "REGION"
        value = var.region
      }
      
      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
        cpu_idle = true
      }
      
      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 30
        timeout_seconds       = 10
        period_seconds        = 10
        failure_threshold     = 3
      }
      
      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 30
        timeout_seconds       = 10
        period_seconds        = 30
        failure_threshold     = 3
      }
    }
  }
  
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# Cloud Run service IAM
resource "google_cloud_run_service_iam_member" "run_invoker" {
  service  = google_cloud_run_v2_service.youtube_automation.name
  location = google_cloud_run_v2_service.youtube_automation.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Scheduler job
resource "google_cloud_scheduler_job" "youtube_automation_scheduler" {
  name        = "${var.service_name}-scheduler"
  description = "Trigger YouTube automation every 6 hours"
  schedule    = "0 */6 * * *"
  time_zone   = "Asia/Seoul"
  region      = var.region
  
  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.youtube_automation.uri}/generate"
    
    oidc_token {
      service_account_email = google_service_account.cloud_run_sa.email
    }
  }
}

# Outputs
output "cloud_run_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.youtube_automation.uri
}

output "service_account_email" {
  description = "Email of the service account"
  value       = google_service_account.cloud_run_sa.email
}

output "bucket_name" {
  description = "Name of the Cloud Storage bucket"
  value       = google_storage_bucket.video_storage.name
}
