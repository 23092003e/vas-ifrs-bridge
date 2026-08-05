variable "secret_names" {
  description = "Secret Manager containers; values are added outside Terraform."
  type        = set(string)
  default = [
    "anthropic-api-key",
    "database-url",
    "gemini-api-key",
    "openai-api-key",
    "qdrant-api-key",
    "secret-key",
    "supabase-service-role-key",
    "supabase-url",
  ]
}

resource "google_secret_manager_secret" "runtime" {
  for_each  = var.secret_names
  secret_id = "vas-ifrs-${var.env}-${each.value}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_iam_member" "runtime" {
  for_each  = google_secret_manager_secret.runtime
  project   = var.project_id
  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}
