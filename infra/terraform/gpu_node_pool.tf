variable "gpu_machine_type" {
  description = "Machine type for optional Ollama GPU nodes."
  type        = string
  default     = "n1-standard-8"
}

variable "enable_gpu_node_pool" {
  description = "Create a T4 GPU node pool for Ollama."
  type        = bool
  default     = false
}

resource "google_container_node_pool" "gpu" {
  count = var.enable_gpu_node_pool ? 1 : 0

  name       = "ollama-gpu"
  location   = var.region
  cluster    = google_container_cluster.main.name
  node_count = 1

  autoscaling {
    min_node_count = 0
    max_node_count = 2
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type    = var.gpu_machine_type
    service_account = google_service_account.runtime.email
    oauth_scopes    = ["https://www.googleapis.com/auth/cloud-platform"]
    disk_type       = "pd-balanced"
    disk_size_gb    = 200

    guest_accelerator {
      type  = "nvidia-tesla-t4"
      count = 1

      gpu_driver_installation_config {
        gpu_driver_version = "DEFAULT"
      }
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    taint {
      key    = "workload"
      value  = "ollama"
      effect = "NO_SCHEDULE"
    }

    labels = {
      environment = var.env
      workload    = "ollama"
    }
  }
}
