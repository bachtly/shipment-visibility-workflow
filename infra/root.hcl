locals {
  # Subscription ID injected via env var ARM_SUBSCRIPTION_ID (OIDC, no hard-coded creds)
  subscription_id = get_env("ARM_SUBSCRIPTION_ID", "")
}

# ---------------------------------------------------------------------------
# Remote state — Azure Storage (create this storage account once manually or
# via a bootstrap script before running terragrunt)
# ---------------------------------------------------------------------------
remote_state {
  backend = "azurerm"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "stshipvistfstate"
    container_name       = "tfstate"
    key                  = "${path_relative_to_include()}/terraform.tfstate"
    use_oidc             = true
  }
}

# ---------------------------------------------------------------------------
# Provider — generated into every env directory
# ---------------------------------------------------------------------------
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<-EOF
    terraform {
      required_providers {
        azurerm = {
          source  = "hashicorp/azurerm"
          version = "~> 4.0"
        }
        random = {
          source  = "hashicorp/random"
          version = "~> 3.6"
        }
      }
      required_version = ">= 1.5"
    }

    provider "azurerm" {
      features {
        resource_group {
          # Azure auto-creates a "Smart Detection" action group inside RGs that
          # contain Application Insights. It isn't in our state, so deleting the
          # RG fails unless we let the provider delete via the Azure API directly.
          prevent_deletion_if_contains_resources = false
        }
      }
      use_oidc = true
    }
  EOF
}

# ---------------------------------------------------------------------------
# Common inputs passed to every module
# ---------------------------------------------------------------------------
inputs = {
  location = "australiaeast"
  tags = {
    project    = "shipment-visibility"
    managed_by = "terraform"
  }
}
