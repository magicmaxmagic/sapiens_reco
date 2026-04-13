# PRD Sapiens Reco - MVP Simplifié

## Objectif

Permettre à un Resource Manager d'obtenir une shortlist de profils en 3 étapes :
1. Import CSV
2. Lancer matching (1 clic)
3. Consulter shortlist triée

---

## Scope MVP

### Inclus ✅

- Authentification simple (login/admin)
- Import profils via CSV
- Import manuel (copier-coller)
- Gestion missions CRUD
- Matching simple par compétences
- Score : 60% skills + 30% seniority + 10% location
- Shortlist triée
- Notes basiques

### Exclus (Phase 2+) 🚧

- Parsing CV automatique
- Intégration ATS/Boond/LinkedIn
- Matching sémantique (embeddings)
- Dashboard analytics
- Feedback structuré
- Multi-tenant
- OpenClaw orchestration

---

## Données

### Profil

| Champ | Type | Obligatoire |
|-------|------|-------------|
| Nom | string | ✅ |
| Email | string | ✅ |
| Compétences | list | - |
| Séniorité | enum (junior/mid/senior) | - |
| Disponibilité | date | - |
| Localisation | string | - |

### Mission

| Champ | Type | Obligatoire |
|-------|------|-------------|
| Titre | string | ✅ |
| Description | text | - |
| Compétences requises | list | - |
| Séniorité requise | enum | - |
| Localisation requise | string | - |
| Statut | enum (open/closed) | - |
| Priorité | int | - |

---

## Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  1. IMPORT  │ ──▶ │  2. MATCH   │ ──▶ │ 3. SHORTLIST│
│   CSV/Manuel│     │   1 clic    │     │  Résultats  │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## Roadmap

| Phase | Durée | Objectif |
|-------|-------|----------|
| MVP | 1-2 semaines | Import CSV → Matching simple → Shortlist |
| V1.5 | +1 semaine | Import manuel (copier-coller) |
| V2 | +2 semaines | Parsing CV (optionnel) |
| V3 | +? | Intégrations externes |

---

## Utilisateurs

| Rôle | Permissions |
|------|-------------|
| **Resource Manager** | Crée missions, lance matching, consulte shortlist |
| **Admin** | Importe profils, gère données |

---

## Architecture Technique

- **Frontend** : Next.js (existant)
- **Backend** : FastAPI (existant)
- **DB** : Supabase PostgreSQL (existant)
- **ML** : ❌ Pas d'embeddings pour le MVP

---

## KPIs MVP

- Nombre de matching runs
- Temps moyen pour obtenir une shortlist
- Taux d'utilisation hebdomadaire
