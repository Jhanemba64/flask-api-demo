# Automatisation du déploiement de conteneurs

[![CI/CD](https://github.com/Jhanemba64/flask-api-demo/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Jhanemba64/flask-api-demo/actions/workflows/ci-cd.yml)

API Flask minimale, testée, dockerisée, analysée, publiée sur **GitHub Container Registry (GHCR)**
avec son SBOM et une attestation de provenance signée, puis déployée sur **Render** via **Terraform**,
le tout orchestré par un pipeline **GitHub Actions**.

```
Code ─▶ Tests (pytest) ─▶ Secrets (gitleaks) + Dockerfile (Hadolint) ─▶ Build ─▶ Scan (Trivy)
     ─▶ SBOM + Push GHCR + provenance signée ─▶ Terraform ─▶ Render
                                          GitHub Actions (CI/CD)
```

## Sommaire

- [Architecture](#architecture)
- [API](#api)
- [Lancer en local](#lancer-en-local)
- [Tests d'intégration](#tests-dintégration)
- [Docker](#docker)
- [Terraform / Render](#terraform--render)
- [Pipeline CI/CD](#pipeline-cicd)
- [Secrets GitHub à configurer](#secrets-github-à-configurer)
- [Licence](#licence)

## Architecture

| Composant            | Fichier(s)                          |
|----------------------|-------------------------------------|
| API Flask            | `app/main.py`                       |
| Tests d'intégration  | `tests/conftest.py`, `tests/test_integration.py` |
| Image conteneur      | `Dockerfile`, `.dockerignore`       |
| Pipeline CI/CD       | `.github/workflows/ci-cd.yml`       |
| Infra Render         | `terraform/*.tf`                    |

## API

| Méthode | Route           | Description                                   |
|---------|-----------------|-----------------------------------------------|
| GET     | `/`             | Message de bienvenue (`"Hello World!"`)       |
| GET     | `/items`        | Liste JSON d'items factices                   |
| POST    | `/items`        | Ajoute un item (`{"name": "..."}`), confirme  |
| DELETE  | `/items/<id>`   | Supprime un item (support du test "suppression") |

> Les 3 routes demandées sont `GET /`, `GET /items`, `POST /items`. La route
> `DELETE /items/<id>` est ajoutée pour couvrir le test d'intégration « suppression d'items ».

## Lancer en local

```bash
python -m venv .venv
# Windows PowerShell : .\.venv\Scripts\Activate.ps1
source .venv/bin/activate
pip install -r requirements-dev.txt

# Serveur de dev
python -m app.main
# ou en mode production
gunicorn --bind 0.0.0.0:5000 app.main:app
```

Tests rapides :

```bash
curl http://localhost:5000/
curl http://localhost:5000/items
curl -X POST http://localhost:5000/items -H "Content-Type: application/json" -d '{"name":"Mon item"}'
curl -X DELETE http://localhost:5000/items/1
```

## Tests d'intégration

Les tests démarrent un **vrai serveur Flask** (thread werkzeug) et l'interrogent via
`requests` — c'est de l'intégration HTTP de bout en bout, pas un client de test mocké.

```bash
pip install -r requirements-dev.txt
pytest -v
```

## Docker

```bash
# Build
docker build -t flask-api-demo .

# Run (l'app lit la variable PORT, défaut 5000)
docker run --rm -p 5000:5000 flask-api-demo

# Test
curl http://localhost:5000/
```

Le `Dockerfile` : base `python:3.13-slim`, installe les dépendances, copie l'API,
expose `5000`, tourne en utilisateur non-root et démarre via gunicorn.

## Terraform / Render

Le code Terraform (`terraform/`) crée :

1. une **registry credential** GHCR (`render_registry_credential`) pour puller l'image privée ;
2. un **service web** Render (`render_web_service`) basé sur l'image GHCR, avec les
   variables d'environnement `PORT` et `APP_NAME` et un health check sur `/`.

### Exécution manuelle

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # puis renseignez vos valeurs
terraform init
terraform plan
terraform apply
```

Récupérer l'URL publique :

```bash
terraform output service_url
```

### Variables principales

| Variable          | Description                                | Défaut          |
|-------------------|--------------------------------------------|-----------------|
| `render_api_key`  | Clé API Render (sensible)                  | —               |
| `render_owner_id` | ID propriétaire Render (user/team)         | —               |
| `image_url`       | `ghcr.io/<owner>/<repo>`                    | —               |
| `image_tag`       | Tag de l'image                             | `latest`        |
| `ghcr_username`   | Compte GitHub pour le pull GHCR            | —               |
| `ghcr_token`      | Token `read:packages` (sensible)           | —               |
| `service_name`    | Nom du service Render                      | `flask-api-demo`|
| `region`          | Région Render                              | `frankfurt`     |
| `plan`            | Plan Render (`free` = sans carte bancaire) | `free`          |

> **État Terraform en CI/CD.** Le runner GitHub est éphémère et perdrait le
> `terraform.tfstate` entre deux runs (Terraform retenterait alors de *créer* des
> ressources déjà existantes → erreur 400). Le workflow **persiste donc le state via le
> cache GitHub Actions** (`actions/cache`), et un step d'amorçage one-shot **importe** les
> ressources déjà créées sur Render si le state est vide. Résultat : chaque push fait un
> *update* (redeploy de la nouvelle image) au lieu d'un *create*.
>
> Le `tfstate` contient des valeurs sensibles (token GHCR) **en clair**. Le dépôt étant
> public, les workflows de pull requests venues de forks peuvent lire le cache de la branche
> principale : le déploiement est donc **désactivé par défaut** (voir [Pipeline CI/CD](#pipeline-cicd)).
> Pour l'activer durablement, passer d'abord à un **backend distant** chiffré (bloc commenté
> dans `versions.tf`, ex. S3 ou Terraform Cloud).

## Pipeline CI/CD

`.github/workflows/ci-cd.yml`, déclenché sur push/PR vers `main` et `workflow_dispatch` :

1. **test** — installe les deps et lance `pytest` (sur push et PR).
2. **securite** — recherche de secrets dans tout l'historique git (**gitleaks**) et
   contrôle des bonnes pratiques du `Dockerfile` (**Hadolint**).
3. **image** — build de l'image, scan **Trivy** bloquant sur les failles critiques et
   élevées corrigeables, **SBOM** SPDX en artefact du run ; hors PR : push sur GHCR (tags
   SHA du commit et `latest`) et **attestation de provenance** signée par Sigstore,
   vérifiable avec `gh attestation verify oci://ghcr.io/jhanemba64/flask-api-demo:latest --owner Jhanemba64`.
4. **deploy** — `terraform init/plan/apply` pour provisionner/déployer sur Render, en
   passant l'image taguée au SHA du commit. **Désactivé par défaut** : il ne tourne sur
   `main` que si la variable de dépôt `RENDER_DEPLOY` vaut `true`
   (`gh variable set RENDER_DEPLOY --body true`).

Sécurité de la chaîne elle-même : droits du `GITHUB_TOKEN` en lecture seule par défaut,
actions épinglées par SHA de commit, mises à jour proposées chaque mois par **Dependabot**
(actions, dépendances Python, image de base, provider Terraform). L'image s'exécute sans
les droits root et pip en est retiré après l'installation des dépendances.

## Secrets GitHub à configurer

Dans **Settings → Secrets and variables → Actions** du dépôt :

| Secret            | Usage                                                                 |
|-------------------|-----------------------------------------------------------------------|
| `RENDER_API_KEY`  | Clé API Render (Dashboard → Account Settings → API Keys).             |
| `RENDER_OWNER_ID` | ID du propriétaire Render (commence par `usr-` ou `tea-`).           |
| `GHCR_TOKEN`      | PAT GitHub avec le scope `read:packages`, stocké par Render pour puller l'image privée. |

> `GITHUB_TOKEN` est fourni automatiquement par Actions et sert au **push** de l'image
> (job *build*). Il est éphémère : Render ayant besoin d'un accès durable au pull, on
> utilise un PAT dédié `GHCR_TOKEN` côté Terraform. (Alternative : rendre le package
> GHCR public, auquel cas la registry credential devient inutile.)

### Créer le dépôt et configurer les secrets en CLI (`gh`)

```bash
gh repo create flask-api-demo --public --source=. --remote=origin --push
gh secret set RENDER_API_KEY  --body "rnd_xxx"
gh secret set RENDER_OWNER_ID --body "tea-xxx"
gh secret set GHCR_TOKEN      --body "ghp_xxx"
```

## Licence

[MIT](LICENSE)
