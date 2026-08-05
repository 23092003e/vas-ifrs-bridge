variable "vpc_cidr" {
  description = "Primary subnet range used by GKE nodes."
  type        = string
  default     = "10.0.0.0/20"
}

variable "pods_cidr" {
  description = "Secondary range used by GKE pods."
  type        = string
  default     = "10.16.0.0/14"
}

variable "services_cidr" {
  description = "Secondary range used by Kubernetes services."
  type        = string
  default     = "10.20.0.0/20"
}

resource "google_compute_network" "main" {
  name                    = local.name
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"

  depends_on = [google_project_service.required]
}

resource "google_compute_subnetwork" "gke" {
  name                     = "${local.name}-gke"
  region                   = var.region
  network                  = google_compute_network.main.id
  ip_cidr_range            = var.vpc_cidr
  private_ip_google_access = true

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.pods_cidr
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.services_cidr
  }
}

resource "google_compute_router" "main" {
  name    = "${local.name}-router"
  region  = var.region
  network = google_compute_network.main.id
}

resource "google_compute_router_nat" "main" {
  name                               = "${local.name}-nat"
  router                             = google_compute_router.main.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}
