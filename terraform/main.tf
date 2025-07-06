provider "google" {
  project = "youtube-fully-automated"
  region  = "us-central1" # Cloud Run 서비스도 us-central1에 배포되도록 일치시킵니다.
}

# ✅ 변수 정의: 프로젝트 ID를 유연하게 사용하기 위해 추가
variable "project_id" {
  description = "The GCP project ID."
  type        = string
  default     = "youtube-fully-automated"
}

# ✅ Cloud Run 서비스 계정 이메일 변수 정의 (코드 가독성 및 유지보수성 향상)
variable "cloud_run_service_account_email" {
  description = "The email of the service account used by Cloud Run."
  type        = string
  default     = "github-actions-sa@youtube-fully-automated.iam.gserviceaccount.com"
}

# 🚀 Cloud Run 서비스 생성 (Terraform 관리 시작!)
resource "google_cloud_run_service" "youtube_shorts_automation" {
  name     = "youtube-shorts-automation" # 서비스 이름은 GitHub Actions YAML과 동일해야 합니다.
  location = var.region                 # provider의 region 변수 사용

  template {
    spec {
      containers {
        # GitHub Actions에서 GCR에 push할 이미지 경로를 참조합니다.
        image = "gcr.io/${var.project_id}/youtube-shorts-automation:latest"
        ports {
          container_port = 8080 # Dockerfile의 EXPOSE 8080과 일치해야 합니다.
        }
      }
      # 이 서비스 계정이 Cloud Run 앱의 권한이 됩니다.
      # 이전에 GitHub Actions에서 사용한 서비스 계정을 Cloud Run 앱의 서비스 계정으로도 활용합니다.
      service_account_name = var.cloud_run_service_account_email
    }
  }

  traffic {
    percent = 100
    latest_revision = true
  }

  # 외부에서 Cloud Run 서비스에 접근 가능하도록 설정 (Pub/Sub Push endpoint 포함)
  # 이는 'allow-unauthenticated'와 같은 역할입니다.
  metadata {
    annotations = {
      "run.googleapis.com/ingress" = "all"
    }
  }

  # Cloud Run 서비스가 배포될 때까지 기다리도록 depends_on 추가
  depends_on = [
    # 필요한 경우, Cloud Run 서비스 계정이 존재함을 명시적으로 지정
    # google_service_account.github_actions_sa (github-actions-sa를 Terraform으로 생성하는 경우)
  ]
}


# ✅ Pub/Sub topic 생성
resource "google_pubsub_topic" "shorts_trigger" {
  name = "shorts-trigger"
}

# ✅ Cloud Scheduler job 생성 (매일 오전 9시 실행 예시)
# 이 스케줄러는 Pub/Sub 토픽으로 메시지를 보냅니다.
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
  
  # Cloud Scheduler Job이 Cloud Run의 Pub/Sub 트리거를 발생시키기 위해
  # Pub/Sub 토픽이 먼저 생성되도록 depends_on 추가
  depends_on = [
    google_pubsub_topic.shorts_trigger
  ]
}

# ✅ Cloud Run 서비스에 Pub/Sub subscriber 역할 부여
# Cloud Run 서비스 계정(github-actions-sa)이 Pub/Sub에서 메시지를 수신할 수 있도록 권한을 줍니다.
resource "google_project_iam_member" "cloudrun_pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${var.cloud_run_service_account_email}"
  
  # 이 IAM 바인딩은 Pub/Sub 구독이 먼저 존재해야 합니다.
  depends_on = [
    google_pubsub_subscription.shorts_trigger_subscription
  ]
}

# ✅ Pub/Sub subscription 생성 → Cloud Run Push endpoint에 전달 (수정됨!)
# Cloud Run 서비스의 동적 URL을 참조하여 푸시 엔드포인트를 설정합니다.
resource "google_pubsub_subscription" "shorts_trigger_subscription" {
  name  = "shorts-trigger-subscription"
  topic = google_pubsub_topic.shorts_trigger.id

  push_config {
    # 🚀 핵심 수정: Cloud Run 서비스의 URL을 동적으로 참조!
    push_endpoint = google_cloud_run_service.youtube_shorts_automation.status[0].url
    
    # Cloud Run 서비스를 호출할 때 사용할 서비스 계정 (oidc_token 사용)
    oidc_token {
      service_account_email = var.cloud_run_service_account_email # Cloud Run 서비스 계정 이메일
    }
  }
  
  # Pub/Sub 구독이 Cloud Run 서비스와 토픽에 의존하도록 설정
  depends_on = [
    google_cloud_run_service.youtube_shorts_automation,
    google_pubsub_topic.shorts_trigger
  ]
}
