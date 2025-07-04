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

variable "cloud_run_service_account_email" {
  description = "Email of the service account used by Cloud Run."
  type        = string
}

resource "google_cloud_scheduler_job" "five_times_daily_youtube_shorts_upload_job" {
  project  = var.project_id
  region   = var.gcp_region
  name     = "five-times-daily-youtube-shorts-upload"
  schedule = "0 21,0,3,6,9 * * *" # 하루 5회 실행 (KST 6,9,12,15,18시)

  http_target {
    uri = "https://${var.gcp_region}-${var.project_id}.run.app/${var.cloud_run_service_name}"
    http_method = "POST"
    headers = {
      "Content-Type" = "application/json"
    }
    body = jsonencode({ "action" = "create_and_upload_shorts" })

    oidc_token {
      service_account_email = var.cloud_run_service_account_email
      audience = "https://${var.gcp_region}-${var.project_id}.run.app/${var.cloud_run_service_name}"
    }
  }
}
