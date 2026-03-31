# Backend Optimus MVP

## Run locally

1. Create environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

If venv is missing on Debian/Ubuntu:

```bash
sudo apt install python3.10-venv
```

2. Set config

```bash
cp .env.example .env
```

3. Run migrations

```bash
alembic upgrade head
```

4. Run API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Open docs

- http://localhost:8000/docs

## Deploy backend on Vercel

Le backend FastAPI peut etre deploye sur Vercel comme projet separe.

Prerequis:
- le fichier [vercel.json](vercel.json) route toutes les requetes vers [api/index.py](api/index.py)
- l'entrypoint [api/index.py](api/index.py) expose l'application FastAPI

Vercel project settings:
- Root Directory: `backend`
- Framework Preset: `Other`

Variables recommandees (Environment Variables Vercel):
- APP_ENV=production
- APP_DEBUG=false
- DATABASE_URL=<supabase-postgres-url-with-sslmode-require>
- ALLOWED_ORIGINS=<frontend-vercel-urls>
- TRUSTED_HOSTS=<backend-vercel-domain>,localhost,127.0.0.1,testserver
- AUTH_REQUIRED=true
- ADMIN_USERNAME=<admin-user>
- ADMIN_PASSWORD=<complex-password>
- ADMIN_PASSWORD_MIN_LENGTH=12
- JWT_SECRET_KEY=<long-random-secret>
- JWT_ALGORITHM=HS256
- JWT_ACCESS_TOKEN_MINUTES=60
- AUDIT_LOG_PATH=/tmp/audit.jsonl

Notes serverless:
- le rate limiting in-memory repart de zero selon les invocations
- le filesystem est ephemere: utiliser `/tmp` pour les fichiers runtime
- les migrations doivent etre appliquees sur la base cible (ex: `alembic upgrade head`)

## Demo seed data

Generate synthetic data for demos (profiles between 50 and 200):

```bash
python -m app.workers.seed_demo_data --reset --profiles 120 --missions 8 --with-matches
```

Useful flags:
- --profiles 50..200
- --missions 1..50
- --reset
- --with-matches
- --seed 42

Example light dataset:

```bash
python -m app.workers.seed_demo_data --reset --profiles 60 --missions 5 --with-matches --seed 7
```

## Security controls

The API includes configurable hardening in app settings:
- trusted host filtering
- in-memory IP rate limiting
- secure HTTP headers
- upload validation (extension/content-type/max size)
- input sanitization for untrusted text fields
- optional prompt-injection hard block
- JWT admin authentication for mutating endpoints
- structured audit journal (JSONL) with export endpoint

Environment variables (see .env.example):
- TRUSTED_HOSTS
- AUTH_REQUIRED
- ADMIN_USERNAME
- ADMIN_PASSWORD
- ADMIN_PASSWORD_MIN_LENGTH
- JWT_SECRET_KEY
- JWT_ALGORITHM
- JWT_ACCESS_TOKEN_MINUTES
- MAX_UPLOAD_SIZE_BYTES
- RATE_LIMIT_MAX_REQUESTS
- RATE_LIMIT_WINDOW_SECONDS
- BLOCK_PROMPT_INJECTION
- AUDIT_LOG_PATH
- AUDIT_EXPORT_MAX_LINES

When AUTH_REQUIRED=true, mutating routes require:
- Authorization: Bearer <token>

Production safety check:
- in APP_ENV=production, API startup fails if ADMIN_PASSWORD or JWT_SECRET_KEY still use defaults.
- in APP_ENV=production, API startup also fails if ADMIN_PASSWORD is weak (min length + uppercase + lowercase + digit + special char).

Get token:

```bash
curl -s -X POST http://localhost:8000/api/auth/login \
	-H "Content-Type: application/json" \
	-d '{"username":"admin","password":"ChangeMe#2026"}'
```

## Main endpoints

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
