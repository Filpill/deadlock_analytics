output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.deadlock_analytics.uri
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.deadlock_analytics.name
}

output "service_location" {
  description = "Location of the Cloud Run service"
  value       = google_cloud_run_v2_service.deadlock_analytics.location
}

output "service_id" {
  description = "Full resource ID of the Cloud Run service"
  value       = google_cloud_run_v2_service.deadlock_analytics.id
}
