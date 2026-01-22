variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "deadlock-485121"
}

variable "region" {
  description = "GCP region for Cloud Run deployment"
  type        = string
  default     = "europe-west2"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "deadlock-analytics"
}

variable "service_account" {
  description = "Service account email for Cloud Run"
  type        = string
  default     = "sa-deadlock-cloud-run@deadlock-485121.iam.gserviceaccount.com"
}

variable "container_image" {
  description = "Container image URL from Artifact Registry"
  type        = string
  default     = "europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo/flask_deadlock_analytics_app:latest"
}

variable "memory" {
  description = "Memory allocation for Cloud Run service"
  type        = string
  default     = "2Gi"
}

variable "cpu" {
  description = "CPU allocation for Cloud Run service"
  type        = string
  default     = "2"
}

variable "timeout" {
  description = "Request timeout in seconds"
  type        = number
  default     = 120
}

variable "min_instances" {
  description = "Minimum number of instances (0 for scale to zero)"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}
