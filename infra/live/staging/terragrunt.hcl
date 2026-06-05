include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "../../modules/azure-stack"
}

inputs = {
  env = "staging"

  # Production-shaped: General Purpose Postgres, always-on Container App
  postgres_sku        = "GP_Standard_D2s_v3"
  postgres_storage_mb = 65536
  min_replicas        = 1
  max_replicas        = 5

  dbos_conductor_key = get_env("DBOS_CONDUCTOR_KEY", "")
}
