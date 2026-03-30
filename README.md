# Optimus MVP

Plateforme de recommandation de profils pour resource managers.

Ce repository contient un socle MVP local-first avec:
- frontend Next.js (UI Dashboard, Profils, Missions & Matching)
- backend FastAPI (upload CV, recherche, matching explicable)
- PostgreSQL local via Docker Compose
- CI/CD GitHub Actions + deploy frontend Vercel

## Structure

```
.
├── frontend/                # Next.js + Tailwind
├── backend/                 # FastAPI + SQLAlchemy
├── docs/                    # PRD et architecture
├── infra/                   # compose additionnel
├── .github/workflows/       # CI/CD
└── docker-compose.yml       # PostgreSQL local
```

## Prerequisites

- Node.js 20+
- Python 3.10+
- Docker + Docker Compose

## Quickstart local

### 1. Database

```bash
docker compose up -d
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Si venv n'est pas disponible sur Debian/Ubuntu:

```bash
sudo apt install python3.10-venv
```

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Frontend: http://localhost:3000

## Seed demo data (50-200 profils)

Depuis le backend (venv active):

```bash
cd backend
python -m app.workers.seed_demo_data --reset --profiles 120 --missions 8 --with-matches
```

Options utiles:
- --profiles: min 50, max 200
- --missions: min 1, max 50
- --reset: purge profils/missions/matches avant generation
- --with-matches: pre-calcule une shortlist initiale
- --seed: random seed pour dataset deterministe

Exemple dataset plus leger:

```bash
python -m app.workers.seed_demo_data --reset --profiles 60 --missions 5 --with-matches --seed 7
```

## Endpoints MVP

- POST /api/profiles/upload
- GET /api/profiles
- GET /api/profiles/{id}
- PATCH /api/profiles/{id}
- POST /api/profiles/{id}/manual-correction
- POST /api/auth/login
- GET /api/auth/me
- POST /api/missions
- GET /api/missions
- GET /api/missions/{id}
- PATCH /api/missions/{id}
- POST /api/missions/{id}/match
- GET /api/missions/{id}/matches
- GET /api/search/profiles?q=python
- GET /api/audit/logs/export?format=json|jsonl

## Matching V1

Score final explicable:
- 40% compatibilite structuree
- 40% similarite semantique texte
- 20% bonus metier simple

Retour:
- top N profils tries
- score detaille
- tags d'explication

## CI/CD

- frontend-ci.yml: lint + typecheck + build
- backend-ci.yml: ruff + tests
- vercel-deploy.yml: deploy frontend sur main

Secrets GitHub requis pour Vercel:
- VERCEL_TOKEN
- VERCEL_ORG_ID
- VERCEL_PROJECT_ID

Variable runtime a definir dans le projet Vercel:
- NEXT_PUBLIC_API_URL=https://your-backend-public-url/api

## Security baseline

Le backend applique un hardening MVP configurable:
- trusted hosts (middleware)
- rate limiting in-memory par IP
- validation stricte upload CV (extension/content-type/taille)
- sanitization de texte entrant (retrait de patterns de prompt-injection)
- headers de securite HTTP
- authentification admin JWT sur les routes mutatives
- journal d'audit structure (JSONL) avec endpoint d'export

Variables de securite dans backend/.env:
- TRUSTED_HOSTS=localhost,127.0.0.1
- AUTH_REQUIRED=true
- ADMIN_USERNAME=admin
- ADMIN_PASSWORD=change-me
- JWT_SECRET_KEY=change-this-jwt-secret-in-prod
- JWT_ALGORITHM=HS256
- JWT_ACCESS_TOKEN_MINUTES=60
- MAX_UPLOAD_SIZE_BYTES=5000000
- RATE_LIMIT_MAX_REQUESTS=180
- RATE_LIMIT_WINDOW_SECONDS=60
- BLOCK_PROMPT_INJECTION=false
- AUDIT_LOG_PATH=logs/audit.jsonl
- AUDIT_EXPORT_MAX_LINES=5000

Flux admin JWT:
1. POST /api/auth/login avec username/password
2. Recuperer access_token
3. Appeler les endpoints mutatifs avec Authorization: Bearer <access_token>

Protection production:
- en APP_ENV=production, l'API refuse de demarrer si ADMIN_PASSWORD ou JWT_SECRET_KEY gardent leur valeur par defaut.

Exemple rapide:

```bash
curl -s -X POST http://localhost:8000/api/auth/login \
	-H "Content-Type: application/json" \
	-d '{"username":"admin","password":"change-me"}'
```

Test de deploiement sur main:
1. merger une PR qui modifie frontend/**
2. verifier le workflow "Deploy Frontend to Vercel"
3. verifier la mise en production sur l'URL Vercel

## Documents

- docs/PRD.md
- docs/architecture.md
