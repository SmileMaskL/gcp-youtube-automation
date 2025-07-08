# terraform/main.tf

provider "google" {
  project = var.project_id # 변수를 사용하여 프로젝트 ID를 지정합니다.
  region  = "us-central1"  # Cloud Run 서비스도 us-central1에 배포되도록 일치시킵니다.
}

# ✅ Cloud Run 서비스 계정 이메일 변수 정의 (코드 가독성 및 유지보수성 향상)
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

# 🚀 Cloud Run 서비스 생성 (Terraform 관리 시작!)
resource "google_cloud_run_service" "youtube_shorts_automation" {
  name     = "youtube-shorts-automation" # 서비스 이름은 GitHub Actions YAML과 동일해야 합니다.
  location = var.region                  # provider의 region 변수 사용

  template {
    spec {
      containers {
        # GitHub Actions에서 GCR에 push할 이미지 경로를 참조합니다.
        image = "gcr.io/${var.project_id}/youtube-shorts-automation:latest"
        ports {
          container_port = 8080 # Dockerfile의 EXPOSE 8080과 일치해야 합니다.
        }
        env { # ✅ 이 블록을 추가하여 환경 변수를 전달합니다.
          name  = "GEMINI_API_KEY"
          value = var.gemini_api_key
        }
        env {
          name  = "ELEVENLABS_API_KEY"
          value = var.elevenlabs_api_key
        }
        # 필요한 다른 secret들을 여기에 추가할 수 있습니다.
      }
      # 이 서비스 계정이 Cloud Run 앱의 권한이 됩니다.
      service_account_name = var.cloud_run_service_account_email
    }
  }

  traffic {
    percent = 100
    latest_revision = true
  }

  # 외부에서 Cloud Run 서비스에 접근 가능하도록 설정 (Pub/Sub Push endpoint 포함)
  metadata {
    annotations = {
      "run.googleapis.com/ingress" = "all"
    }
  }

  # Cloud Run 서비스가 배포될 때까지 기다리도록 depends_on 추가
  depends_on = [] # 이 부분은 명시적인 종속성이 없으므로 비워둡니다.
}

# ✅ Pub/Sub topic 생성
resource "google_pubsub_topic" "shorts_trigger" {
  name = "shorts-trigger"
}

# ✅ Cloud Scheduler job 생성 (매일 오전 9시 실행 예시)
resource "google_cloud_scheduler_job" "daily_shorts_trigger" {
  name        = "daily-shorts-trigger"
  description = "매일 유튜브 쇼츠 자동 업로드 트리거"
  schedule    = "0 9 * * *" # 한국 시간 오전 9시 (UTC 0시)
  time_zone   = "Asia/Seoul"

  pubsub_target {
    topic_name = google_pubsub_topic.shorts_trigger.id
    # Cloud Run 서비스에 보낼 데이터 (예: action과 metadata)
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
