terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Cloud Run service
resource "google_cloud_run_v2_service" "deadlock_analytics" {
  name     = var.service_name
  location = var.region

  template {
    service_account = var.service_account

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      ports {
        container_port = 8080
      }

      # Environment variables (if needed)
      # env {
      #   name  = "ENV_VAR_NAME"
      #   value = "value"
      # }
    }

    timeout = "${var.timeout}s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Allow unauthenticated access
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.deadlock_analytics.location
  name     = google_cloud_run_v2_service.deadlock_analytics.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
