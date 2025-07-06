variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "youtube-fully-automated"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "youtube-shorts-automation"
}

variable "scheduler_name" {
  description = "Cloud Scheduler job name"
  type        = string
  default     = "five-times-daily-youtube-shorts-upload"
}

variable "service_account_email" {
  description = "Service account email for OIDC token"
  type        = string
}
