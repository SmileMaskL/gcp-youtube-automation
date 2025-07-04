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
    # Cloud Run 서비스 호출용 URL - 실제 서비스 URL로 변경
    uri = "https://youtube-shorts-automation-94662874801.us-central1.run.app"

    oidc_token {
      service_account_email = var.service_account_email
      # audience는 호출하는 Cloud Run URL과 같아야 함 - 실제 서비스 URL로 변경
      audience = "https://youtube-shorts-automation-94662874801.us-central1.run.app"
    }

    headers = {
      "Content-Type" = "application/json"
    }

    # IMPORTANT: body 필드는 Base64 인코딩되어야 합니다.
    # jsonencode 결과를 base64encode로 다시 인코딩합니다.
    body = base64encode(jsonencode({
      action   = "create_and_upload_shorts",
      metadata = {
        source = "scheduler"
      }
    }))
  }
}
