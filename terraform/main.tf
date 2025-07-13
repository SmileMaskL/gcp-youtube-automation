# terraform/main.tf

provider "google" {
  project = var.project_id
  region  = "us-central1" # ✅ us-central1로 명확히 설정
}

# ✅ Artifact Registry Repository 생성 리소스 추가
resource "google_artifact_registry_repository" "youtube_shorts_automation_repo" {
  repository_id = "youtube-shorts-automation"
  location      = "us-central1" # ✅ us-central1로 통일
  format        = "DOCKER"
  description   = "Docker repository for YouTube Shorts Automation"
}

# ✅ Cloud Run 서비스 계정 이메일 변수 정의
variable "cloud_run_service_account_email" {
  description = "The email of the service account used by Cloud Run."
  type        = string
  default     = "github-actions-sa@youtube-fully-automated.iam.gserviceaccount.com"
}

# ✅ API 키 변수 정의 (variables.tf 파일에 정의 필요)
variable "gemini_api_key" {
  description = "API Key for Gemini."
  type        = string
  sensitive   = true
}

variable "elevenlabs_api_key" {
  description = "API Key for ElevenLabs."
  type        = string
  sensitive   = true
}

# 🚀 Cloud Run 서비스 생성
resource "google_cloud_run_service" "youtube_shorts_automation" {
  name     = "youtube-shorts-automation"
  location = var.region # ✅ provider의 region 변수 사용

  template {
    spec {
      containers {
        # ✅ Artifact Registry 이미지를 참조하도록 변경
        image = "${google_artifact_registry_repository.youtube_shorts_automation_repo.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.youtube_shorts_automation_repo.repository_id}/${google_cloud_run_service.youtube_shorts_automation.name}:latest"
        ports {
          container_port = 8080
        }
        env {
          name  = "GEMINI_API_KEY"
          value = var.gemini_api_key
        }
        env {
          name  = "ELEVENLABS_API_KEY"
          value = var.elevenlabs_api_key
        }
        # 필요한 다른 secret들을 여기에 추가할 수 있습니다.
      }
      service_account_name = var.cloud_run_service_account_email
    }
  }

  traffic {
    percent = 100
    latest_revision = true
  }

  metadata {
    annotations = {
      "run.googleapis.com/ingress" = "all"
    }
  }

  depends_on = [
    google_artifact_registry_repository.youtube_shorts_automation_repo # ✅ Artifact Registry repo에 대한 종속성 추가
  ]
}

# Pub/Sub topic 및 Scheduler, Subscription 등은 region에 크게 영향받지 않으므로 그대로 유지
# 단, google_cloud_scheduler_job의 time_zone은 "Asia/Seoul"이 아닌 "America/Chicago" 등으로 변경해야 us-central1에 맞게 됩니다.
resource "google_cloud_scheduler_job" "daily_shorts_trigger" {
  name        = "daily-shorts-trigger"
  description = "매일 유튜브 쇼츠 자동 업로드 트리거"
  schedule    = "0 9 * * *" # 원하는 시간으로 설정
  time_zone   = "America/Chicago" # ✅ us-central1에 맞는 타임존으로 변경

  pubsub_target {
    topic_name = google_pubsub_topic.shorts_trigger.id
    data       = base64encode(jsonencode({"action":"create_and_upload_shorts", "metadata":{"topic":"긍정 명언"}}))
  }
  depends_on = [
    google_pubsub_topic.shorts_trigger
  ]
}

# ✅ Pub/Sub subscription 생성 → Cloud Run Push endpoint에 전달 (수정됨!)
resource "google_pubsub_subscription" "shorts_trigger_subscription" {
  name  = "shorts-trigger-subscription"
  topic = google_pubsub_topic.shorts_trigger.id

  push_config {
    push_endpoint = google_cloud_run_service.youtube_shorts_automation.status[0].url
    
    oidc_token {
      service_account_email = var.cloud_run_service_account_email # Cloud Run 서비스 계정 이메일
    }
  }
  
  depends_on = [
    google_cloud_run_service.youtube_shorts_automation,
    google_pubsub_topic.shorts_trigger
  ]
}

# ✅ Cloud Run 서비스에 Pub/Sub subscriber 역할 부여
# Cloud Run 서비스 계정(github-actions-sa)이 Pub/Sub에서 메시지를 수신할 수 있도록 권한을 줍니다.
resource "google_project_iam_member" "cloudrun_pubsub_subscriber" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator" # Pub/Sub 푸시 요청에 OIDC 토큰을 생성하기 위해 필요
  member  = "serviceAccount:service-${var.project_id}@gcp-sa-pubsub.iam.gserviceaccount.com" # Pub/Sub 서비스 계정
}

resource "google_project_iam_member" "cloudrun_invoker_for_pubsub" {
  project = var.project_id
  role    = "roles/run.invoker" # Pub/Sub 서비스 계정이 Cloud Run 서비스를 호출할 수 있도록 권한을 줍니다.
  member  = "serviceAccount:service-${var.project_id}@gcp-sa-pubsub.iam.gserviceaccount.com" # Pub/Sub 서비스 계정

  depends_on = [
    google_cloud_run_service.youtube_shorts_automation
  ]
}
