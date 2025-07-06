provider "google" {
  project = "youtube-fully-automated"
  region  = "us-central1"
}

# ✅ Pub/Sub topic 생성
resource "google_pubsub_topic" "shorts_trigger" {
  name = "shorts-trigger"
}

# ✅ Cloud Scheduler job 생성 (매일 오전 9시 실행 예시)
resource "google_cloud_scheduler_job" "daily_shorts_trigger" {
  name             = "daily-shorts-trigger"
  description      = "매일 유튜브 쇼츠 자동 업로드 트리거"
  schedule         = "0 9 * * *" # 서울 오전 9시 → UTC 0시
  time_zone        = "Asia/Seoul"

  pubsub_target {
    topic_name = google_pubsub_topic.shorts_trigger.id
    data       = base64encode("{\"action\":\"create_and_upload_shorts\", \"metadata\":{\"topic\":\"긍정 명언\"}}")
  }
}

# ✅ Cloud Run 서비스에 Pub/Sub subscriber 역할 부여
resource "google_project_iam_member" "cloudrun_pubsub_subscriber" {
  project = "youtube-fully-automated"
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:github-actions-sa@youtube-fully-automated.iam.gserviceaccount.com"
}

# ✅ Pub/Sub subscription 생성 → Cloud Run Push endpoint에 전달
resource "google_pubsub_subscription" "shorts_trigger_subscription" {
  name  = "shorts-trigger-subscription"
  topic = google_pubsub_topic.shorts_trigger.id

  push_config {
    push_endpoint = "https://youtube-shorts-automation-94662874801.us-central1.run.app"
    oidc_token {
      service_account_email = "github-actions-sa@youtube-fully-automated.iam.gserviceaccount.com"
    }
  }
}
