provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_cloud_scheduler_job" "five_times_daily_youtube_shorts_upload_job" {
  name        = var.scheduler_name
  description = "Run YouTube Shorts upload 5 times daily"
  schedule    = "0 0,6,12,18,23 * * *"  # KST 기준 0시,6시,12시,18시,23시 실행
  time_zone   = "Asia/Seoul"
  project     = var.project_id
  region      = var.region

  http_target {
    http_method = "POST"
    # Cloud Run 서비스 호출용 URL - Cloud Run REST API invoke endpoint 형태
    uri = "https://${var.region}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/${var.project_id}/services/${var.service_name}:invoke"

    oidc_token {
      service_account_email = var.service_account_email
      # audience는 호출하는 Cloud Run URL과 같아야 함
      audience = "https://${var.region}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/${var.project_id}/services/${var.service_name}:invoke"
    }

    headers = {
      "Content-Type" = "application/json"
    }

    body = jsonencode({
      action   = "create_and_upload_shorts",
      metadata = {
        source = "scheduler"
      }
    })
  }
}
