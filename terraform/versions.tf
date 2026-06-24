terraform {
  required_version = ">= 1.5"

  required_providers {
    render = {
      source  = "render-oss/render"
      version = "~> 1.8"
    }
  }

  # ---------------------------------------------------------------------------
  # État distant (recommandé en CI/CD pour des `apply` idempotents).
  # En local / pour la démo, l'état est stocké dans terraform.tfstate.
  # Décommentez et configurez un backend pour conserver l'état entre les runs
  # GitHub Actions (sinon Terraform tente de recréer le service à chaque fois).
  #
  # backend "s3" {
  #   bucket = "mon-bucket-tfstate"
  #   key    = "render/flask-api.tfstate"
  #   region = "eu-west-3"
  # }
  # ---------------------------------------------------------------------------
}
