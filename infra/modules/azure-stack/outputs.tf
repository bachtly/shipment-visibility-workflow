output "container_app_fqdn" {
  description = "Public FQDN of the Container App"
  value       = azurerm_container_app.app.ingress[0].fqdn
}

output "acr_login_server" {
  description = "ACR login server URL"
  value       = azurerm_container_registry.acr.login_server
}

output "postgres_fqdn" {
  description = "Postgres server FQDN (private)"
  value       = azurerm_postgresql_flexible_server.postgres.fqdn
}

output "resource_group_name" {
  value = azurerm_resource_group.rg.name
}
