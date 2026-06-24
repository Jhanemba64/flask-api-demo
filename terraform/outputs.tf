output "service_id" {
  description = "Identifiant du service Render créé."
  value       = render_web_service.api.id
}

output "service_url" {
  description = "URL publique du service déployé sur Render."
  value       = render_web_service.api.url
}

output "registry_credential_id" {
  description = "Identifiant de la credential de registre GHCR."
  value       = render_registry_credential.ghcr.id
}
