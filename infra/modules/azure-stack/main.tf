locals {
  prefix = "shipvis-${var.env}"
  db_name = "shipvis"
  db_user = "shipvisadmin"
}

# --------------------------------------------------------------------------
# Resource group
# --------------------------------------------------------------------------
resource "azurerm_resource_group" "rg" {
  name     = "rg-${local.prefix}"
  location = var.location
  tags     = var.tags
}

# --------------------------------------------------------------------------
# Networking
# --------------------------------------------------------------------------
resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-${local.prefix}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  address_space       = ["10.0.0.0/16"]
  tags                = var.tags
}

resource "azurerm_subnet" "aca" {
  name                 = "snet-aca"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.0.0/23"]
  delegation {
    name = "aca-delegation"
    service_delegation {
      name    = "Microsoft.App/environments"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

resource "azurerm_subnet" "postgres" {
  name                 = "snet-postgres"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.2.0/24"]
  delegation {
    name = "postgres-delegation"
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

resource "azurerm_private_dns_zone" "postgres" {
  name                = "${local.prefix}.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.rg.name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "link-postgres"
  resource_group_name   = azurerm_resource_group.rg.name
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  virtual_network_id    = azurerm_virtual_network.vnet.id
}

# --------------------------------------------------------------------------
# Container Registry
# --------------------------------------------------------------------------
resource "azurerm_container_registry" "acr" {
  name                = replace("acr${local.prefix}", "-", "")
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = false
  tags                = var.tags
}

# --------------------------------------------------------------------------
# Managed identity (for ACR pull + Key Vault access)
# --------------------------------------------------------------------------
resource "azurerm_user_assigned_identity" "app" {
  name                = "id-${local.prefix}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  tags                = var.tags
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}

# --------------------------------------------------------------------------
# Key Vault
# --------------------------------------------------------------------------
data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "kv" {
  name                        = "kv-${local.prefix}"
  resource_group_name         = azurerm_resource_group.rg.name
  location                    = azurerm_resource_group.rg.location
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"
  purge_protection_enabled    = false
  soft_delete_retention_days  = 7
  tags                        = var.tags

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id
    secret_permissions = ["Get", "Set", "Delete", "List", "Purge", "Recover"]
  }

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = azurerm_user_assigned_identity.app.principal_id
    secret_permissions = ["Get"]
  }
}

resource "azurerm_key_vault_secret" "conductor_key" {
  name         = "dbos-conductor-key"
  value        = var.dbos_conductor_key
  key_vault_id = azurerm_key_vault.kv.id
}

resource "azurerm_key_vault_secret" "db_password" {
  name         = "db-password"
  value        = random_password.db.result
  key_vault_id = azurerm_key_vault.kv.id
}

resource "random_password" "db" {
  length  = 24
  special = false
}

# --------------------------------------------------------------------------
# PostgreSQL Flexible Server
# --------------------------------------------------------------------------
resource "azurerm_postgresql_flexible_server" "postgres" {
  name                   = "psql-${local.prefix}"
  resource_group_name    = azurerm_resource_group.rg.name
  location               = azurerm_resource_group.rg.location
  version                = "16"
  administrator_login    = local.db_user
  administrator_password = random_password.db.result
  sku_name               = var.postgres_sku
  storage_mb             = var.postgres_storage_mb
  delegated_subnet_id    = azurerm_subnet.postgres.id
  private_dns_zone_id    = azurerm_private_dns_zone.postgres.id
  zone                   = "1"
  tags                   = var.tags

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = local.db_name
  server_id = azurerm_postgresql_flexible_server.postgres.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# --------------------------------------------------------------------------
# Log Analytics + Application Insights
# --------------------------------------------------------------------------
resource "azurerm_log_analytics_workspace" "logs" {
  name                = "law-${local.prefix}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

resource "azurerm_application_insights" "ai" {
  name                = "ai-${local.prefix}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  workspace_id        = azurerm_log_analytics_workspace.logs.id
  application_type    = "web"
  tags                = var.tags
}

# --------------------------------------------------------------------------
# Container Apps Environment
# --------------------------------------------------------------------------
resource "azurerm_container_app_environment" "env" {
  name                       = "cae-${local.prefix}"
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = azurerm_resource_group.rg.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id
  infrastructure_subnet_id   = azurerm_subnet.aca.id
  tags                       = var.tags
}

# --------------------------------------------------------------------------
# Container App
# --------------------------------------------------------------------------
locals {
  db_url = "postgresql://${local.db_user}:${random_password.db.result}@${azurerm_postgresql_flexible_server.postgres.fqdn}:5432/${local.db_name}?sslmode=require"
}

resource "azurerm_container_app" "app" {
  name                         = "ca-${local.prefix}"
  resource_group_name          = azurerm_resource_group.rg.name
  container_app_environment_id = azurerm_container_app_environment.env.id
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app.id]
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.app.id
  }

  secret {
    name  = "db-url"
    value = local.db_url
  }

  secret {
    name  = "conductor-key"
    value = var.dbos_conductor_key
  }

  template {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name   = "app"
      image  = var.container_image != "" ? var.container_image : "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name        = "DBOS_SYSTEM_DATABASE_URL"
        secret_name = "db-url"
      }
      env {
        name        = "DATABASE_URL"
        secret_name = "db-url"
      }
      env {
        name        = "DBOS_CONDUCTOR_KEY"
        secret_name = "conductor-key"
      }
    }

    http_scale_rule {
      name                = "http-scaler"
      concurrent_requests = "10"
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8080
    transport        = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  depends_on = [azurerm_role_assignment.acr_pull]
}
