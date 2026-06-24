variable "render_api_key" {
  description = "Clé API Render (Dashboard > Account Settings > API Keys)."
  type        = string
  sensitive   = true
}

variable "render_owner_id" {
  description = "ID du propriétaire Render (utilisateur ou équipe) des ressources."
  type        = string
}

variable "image_url" {
  description = "URL de l'image GHCR sans le tag, ex : ghcr.io/owner/repo."
  type        = string
}

variable "image_tag" {
  description = "Tag de l'image à déployer (ex : un SHA de commit ou 'latest')."
  type        = string
  default     = "latest"
}

variable "ghcr_username" {
  description = "Compte GitHub utilisé par Render pour puller l'image GHCR."
  type        = string
}

variable "ghcr_token" {
  description = "Token GitHub (scope read:packages) pour puller l'image privée GHCR."
  type        = string
  sensitive   = true
}

variable "service_name" {
  description = "Nom du service web Render."
  type        = string
  default     = "flask-api-demo"
}

variable "region" {
  description = "Région Render : frankfurt, ohio, oregon, singapore, virginia."
  type        = string
  default     = "frankfurt"
}

variable "plan" {
  description = "Plan Render : free, starter, standard, pro, ... (free = sans carte bancaire)."
  type        = string
  default     = "free"
}

variable "app_port" {
  description = "Port sur lequel l'application écoute dans le conteneur."
  type        = string
  default     = "5000"
}
