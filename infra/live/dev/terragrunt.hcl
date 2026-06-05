include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "../../modules/azure-stack"
}

inputs = {
  env = "dev"

  # Cheapest Postgres SKU; scale-to-zero for the Container App
  postgres_sku        = "B_Standard_B1ms"
  postgres_storage_mb = 32768
  min_replicas        = 0
  max_replicas        = 2

  # Set DBOS_CONDUCTOR_KEY env var at plan/apply time (or via CI secret)
  dbos_conductor_key = get_env("DBOS_CONDUCTOR_KEY", "")
}
