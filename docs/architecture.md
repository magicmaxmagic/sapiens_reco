# Architecture MVP - Optimus

## 1. Vue d'ensemble

Le MVP suit une architecture simple, monolithique et local-first:

- frontend Next.js (UI RM/Admin)
- backend FastAPI (API + matching)
- PostgreSQL (profils, missions, resultats)
- stockage local fichiers CV

## 2. Flux principal

1. upload CV (PDF/DOCX) via API
2. parsing texte + extraction basique
3. persistance Profile
4. creation Mission
5. lancement matching mission -> profils
6. consultation shortlist dans frontend

## 3. Composants

### Frontend

- Dashboard
- Profils
- Missions & Matching
- client API server-side rendering

### Backend

- app/api/endpoints: routes REST
- app/services/parsing_service: extraction CV
- app/services/search_service: recherche + filtres
- app/services/matching_service: scoring V1 explicable
- app/models: SQLAlchemy entities

### Data model

- Profile 1:N Experience
- Mission 1:N MatchResult
- Profile 1:N MatchResult

## 4. Contrats API MVP

- POST /api/profiles/upload
- GET /api/profiles
- GET /api/profiles/{id}
- PATCH /api/profiles/{id}
- POST /api/profiles/{id}/manual-correction
- POST /api/missions
- GET /api/missions
- GET /api/missions/{id}
- PATCH /api/missions/{id}
- POST /api/missions/{id}/match
- GET /api/missions/{id}/matches
- GET /api/search/profiles?q=...

## 5. CI/CD

- frontend-ci.yml: lint + typecheck + build
- backend-ci.yml: ruff + tests
- vercel-deploy.yml: deploy frontend on main

## 6. Deploiement

- local: frontend + backend + postgres docker
- demo: frontend Vercel, backend public test endpoint

## 7. Evolutions post-MVP

- extraction CV plus robuste
- recherche full-text avancee + embeddings
- auth et roles
- connecteurs ATS externes

## 8. Securite & auditabilite (etat MVP)

- boundary claire: tout texte CV/mission est traite comme non fiable
- sanitization en entree pour champs texte et listes
- detection de patterns de prompt-injection (signals)
- mode blocage optionnel via BLOCK_PROMPT_INJECTION=true
- validation stricte des uploads (taille/extension/content-type)
- rate limiting et trusted hosts au niveau middleware
- logs de requete avec request-id pour correlation audit
- authentification admin JWT sur endpoints mutatifs
- journal d'audit structure JSONL + export API

Limites connues MVP:
- rate limit in-memory (non distribue)
- pas encore de RBAC complet ni d'auth utilisateur finale
- controles anti-prompt-injection orientes hygiene d'entree, a renforcer si orchestration LLM multi-etapes
