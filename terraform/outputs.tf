# terraform/outputs.tf (수정된 버전)

output "scheduler_job_name" {
  description = "Cloud Scheduler job name"
  # ✅ 'five_times_daily_youtube_shorts_upload_job' 대신 'daily_shorts_trigger'로 수정!
  value       = google_cloud_scheduler_job.daily_shorts_trigger.name
}
