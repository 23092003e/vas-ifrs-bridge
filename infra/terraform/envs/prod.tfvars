project_id           = "vas-ifrs-prod"
env                  = "prod"
enable_gpu_node_pool = true
gke_control_plane_authorized_cidrs = [
  {
    # TEST-NET is intentionally unreachable; replace with a trusted runner CIDR.
    cidr_block   = "192.0.2.1/32"
    display_name = "replace-before-apply"
  }
]
