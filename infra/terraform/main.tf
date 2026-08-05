terraform {
  required_version = ">= 1.9"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 6.0" }
  }
  backend "gcs" {
    bucket = "vifb-tfstate"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "Google Cloud project ID."
  type        = string
}

variable "env" {
  description = "Deployment environment name."
  type        = string

  validation {
    condition     = contains(["staging", "prod"], var.env)
    error_message = "env must be either staging or prod."
  }
}

variable "region" {
  description = "Google Cloud region for regional resources."
  type        = string
  default     = "asia-southeast1"
}

locals {
  name = "vas-ifrs-${var.env}"
}

resource "google_project_service" "required" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "compute.googleapis.com",
    "container.googleapis.com",
    "iamcredentials.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "sts.googleapis.com",
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
