output "scheduler_job_name" {
  description = "Cloud Scheduler job name"
  value       = google_cloud_scheduler_job.five_times_daily_youtube_shorts_upload_job.name
}
