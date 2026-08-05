variable "gcs_location" {
  description = "Location for document and export buckets."
  type        = string
  default     = "ASIA-SOUTHEAST1"
}

resource "google_storage_bucket" "documents" {
  name                        = "${var.project_id}-${var.env}-vas-ifrs-docs"
  location                    = var.gcs_location
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

resource "google_storage_bucket" "exports" {
  name                        = "${var.project_id}-${var.env}-vas-ifrs-exports"
  location                    = var.gcs_location
  uniform_bucket_level_access = true
  force_destroy               = false

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}
