# PRD - Optimus MVP

## 1. Vision

Optimus aide les resource managers a centraliser des CV, rechercher rapidement des profils, lancer un matching explicable et produire une shortlist exploitable.

## 2. Objectif MVP

Prouver qu'a partir d'une mission et d'un stock CV local, le systeme fournit une shortlist pertinente plus rapidement qu'une recherche manuelle.

## 3. Scope MVP

Inclus:
- import CV PDF/DOCX
- parsing texte + extraction basique
- CRUD missions
- recherche profils (texte + filtres)
- matching V1 explicable
- shortlist top 10
- frontend deployable sur Vercel
- CI/CD GitHub Actions front/back

Exclus:
- communication consultants
- disponibilites automatisees
- connecteurs ATS live
- SSO enterprise
- modeles ML avances (two-tower, RAG)

## 4. Personas

- Resource Manager: cree une mission, lance le matching, lit la shortlist.
- Admin/Ops: importe des CV, corrige les champs parses.

## 5. User Stories cle

- En tant qu'admin, je peux importer un CV PDF/DOCX et visualiser les champs extraits.
- En tant qu'admin, je peux corriger manuellement un profil et enregistrer les champs ajustes.
- En tant que RM, je peux creer/editer une mission avec contraintes metier.
- En tant que RM, je peux rechercher des profils avec filtres metier.
- En tant que RM, je peux lancer un matching et obtenir un top 10 avec explications.

## 6. Matching V1

Pipeline:
1. normalisation mission
2. filtres structures
3. similarite texte mission/CV
4. score final explicable

Score cible:
- 40% compatibilite structuree
- 40% similarite semantique texte
- 20% bonus metier simple

Sortie:
- top 10 profils
- score final
- tags de justification

## 7. Stack cible

- Frontend: Next.js, TypeScript, Tailwind
- Backend: FastAPI, SQLAlchemy, Alembic
- DB: PostgreSQL local (Docker Compose)
- Parsing: pypdf, python-docx, regles metier
- Matching: TF-IDF + regles explicables
- CI/CD: GitHub Actions
- Deploy front: Vercel

## 8. Definition of Done MVP

Le MVP est pret quand:
- un lot de 50 a 200 CV peut etre importe
- les profils structures sont consultables
- une mission peut etre creee
- la shortlist top 10 est generee avec score
- le frontend est deploye sur Vercel
- la CI front/back passe sur PR
