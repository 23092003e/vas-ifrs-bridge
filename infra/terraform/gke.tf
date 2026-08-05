variable "gke_node_count" {
  description = "Initial and minimum node count for the general node pool."
  type        = number
  default     = 2
}

variable "gke_max_node_count" {
  description = "Maximum node count for the general node pool."
  type        = number
  default     = 6
}

variable "gke_machine_type" {
  description = "Machine type for application nodes."
  type        = string
  default     = "e2-standard-4"
}

resource "google_container_cluster" "main" {
  name     = local.name
  location = var.region

  network    = google_compute_network.main.id
  subnetwork = google_compute_subnetwork.gke.id

  remove_default_node_pool = true
  initial_node_count       = 1
  deletion_protection      = var.env == "prod"

  release_channel {
    channel = "REGULAR"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  master_authorized_networks_config {
    dynamic "cidr_blocks" {
      for_each = var.gke_control_plane_authorized_cidrs
      content {
        cidr_block   = cidr_blocks.value.cidr_block
        display_name = cidr_blocks.value.display_name
      }
    }
  }

  depends_on = [google_project_service.required]
}

variable "gke_control_plane_authorized_cidrs" {
  description = "CIDRs allowed to reach the public GKE control-plane endpoint."
  type = list(object({
    cidr_block   = string
    display_name = string
  }))

  validation {
    condition     = length(var.gke_control_plane_authorized_cidrs) > 0
    error_message = "At least one trusted control-plane CIDR is required."
  }
}

resource "google_container_node_pool" "general" {
  name       = "general"
  location   = var.region
  cluster    = google_container_cluster.main.name
  node_count = var.gke_node_count

  autoscaling {
    min_node_count = var.gke_node_count
    max_node_count = var.gke_max_node_count
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type    = var.gke_machine_type
    service_account = google_service_account.runtime.email
    oauth_scopes    = ["https://www.googleapis.com/auth/cloud-platform"]
    disk_type       = "pd-balanced"
    disk_size_gb    = 100

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    labels = {
      environment = var.env
      workload    = "general"
    }
  }
}
