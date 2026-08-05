resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "vas-ifrs"
  description   = "Immutable VAS-IFRS application images"
  format        = "DOCKER"

  cleanup_policies {
    id     = "delete-untagged"
    action = "DELETE"
    condition {
      tag_state  = "UNTAGGED"
      older_than = "2592000s"
    }
  }

  depends_on = [google_project_service.required]
}

output "artifact_registry_repository" {
  value = google_artifact_registry_repository.containers.repository_id
}

output "gke_cluster_name" {
  value = google_container_cluster.main.name
}

output "runtime_service_account" {
  value = google_service_account.runtime.email
}

output "github_workload_identity_provider" {
  value = google_iam_workload_identity_pool_provider.github.name
}

output "deploy_service_account" {
  value = google_service_account.deploy.email
}
