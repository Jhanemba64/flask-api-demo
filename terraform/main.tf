provider "render" {
  api_key  = var.render_api_key
  owner_id = var.render_owner_id
}

# Identifiants permettant à Render de puller l'image privée depuis GHCR.
resource "render_registry_credential" "ghcr" {
  name       = "${var.service_name}-ghcr"
  registry   = "GITHUB"
  username   = var.ghcr_username
  auth_token = var.ghcr_token

  lifecycle {
    # auth_token est en écriture seule (jamais relu) : on ignore sa "dérive"
    # pour que les re-runs ne déclenchent pas d'update inutile.
    ignore_changes = [auth_token]
  }
}

# Service web Render déployé à partir de l'image conteneur GHCR.
resource "render_web_service" "api" {
  name   = var.service_name
  plan   = var.plan
  region = var.region

  runtime_source = {
    image = {
      image_url              = var.image_url
      tag                    = var.image_tag
      registry_credential_id = render_registry_credential.ghcr.id
    }
  }

  # Render interroge cette route pour vérifier la santé du service.
  health_check_path = "/"

  # Variables d'environnement nécessaires à l'application.
  env_vars = {
    PORT     = { value = var.app_port }
    APP_NAME = { value = var.service_name }
  }

  lifecycle {
    # Le tier free de Render n'autorise pas les UPDATE Terraform du service
    # (le provider envoie maintenance_mode, rejeté en free). On ignore donc
    # runtime_source : Terraform ne PROVISIONNE le service qu'à la création,
    # et les déploiements d'images suivants sont déclenchés via l'API Render
    # (étape "Déclencher le deploy" du workflow), avec le tag = SHA du commit.
    ignore_changes = [runtime_source]
  }
}
