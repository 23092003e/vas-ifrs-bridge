variable "github_repository" {
  description = "GitHub repository allowed to deploy through OIDC."
  type        = string
  default     = "23092003e/vas-ifrs-bridge"
}

resource "google_service_account" "runtime" {
  account_id   = "vas-ifrs-${var.env}-runtime"
  display_name = "VAS-IFRS ${var.env} runtime"
}

resource "google_project_iam_member" "runtime_observability" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/artifactregistry.reader",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_storage_bucket_iam_member" "runtime_documents" {
  bucket = google_storage_bucket.documents.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_storage_bucket_iam_member" "runtime_exports" {
  bucket = google_storage_bucket.exports.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_service_account" "deploy" {
  account_id   = "vas-ifrs-${var.env}-deploy"
  display_name = "VAS-IFRS ${var.env} GitHub deployer"
}

resource "google_project_iam_member" "deploy" {
  for_each = toset([
    "roles/artifactregistry.writer",
    "roles/container.developer",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_service_account_iam_member" "deploy_uses_runtime" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-${var.env}"
  display_name              = "GitHub ${var.env} deployments"

  depends_on = [google_project_service.required]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "GitHub Actions"

  attribute_mapping = {
    "google.subject"             = "assertion.sub"
    "attribute.actor"            = "assertion.actor"
    "attribute.repository"       = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
  }
  attribute_condition = "assertion.repository == '${var.github_repository}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "github_deploy" {
  service_account_id = google_service_account.deploy.name
  role               = "roles/iam.workloadIdentityUser"
  member = format(
    "principalSet://iam.googleapis.com/%s/attribute.repository/%s",
    google_iam_workload_identity_pool.github.name,
    var.github_repository,
  )
}
