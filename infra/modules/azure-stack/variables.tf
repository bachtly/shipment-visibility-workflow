variable "env" {
  description = "Environment name (dev | staging)"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "container_image" {
  description = "Fully-qualified ACR image reference (registry/image:tag)"
  type        = string
  default     = ""
}

variable "dbos_conductor_key" {
  description = "DBOS Conductor API key — stored in Key Vault, injected as secret"
  type        = string
  sensitive   = true
  default     = ""
}

# Postgres sizing
variable "postgres_sku" {
  description = "PostgreSQL Flexible Server SKU"
  type        = string
  default     = "B_Standard_B1ms"  # cheapest; override to GP_Standard_D2s_v3 for staging
}

variable "postgres_storage_mb" {
  type    = number
  default = 32768  # 32 GB
}

# Container App scaling
variable "min_replicas" {
  type    = number
  default = 0  # scale to zero in dev
}

variable "max_replicas" {
  type    = number
  default = 3
}
