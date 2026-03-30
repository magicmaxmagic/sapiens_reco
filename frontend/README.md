# Frontend Optimus MVP

## Run locally

```bash
npm install
cp .env.example .env.local
npm run dev
```

App URL:
- http://localhost:3000

Required variable:
- NEXT_PUBLIC_API_URL=http://localhost:8000/api

## Main pages

- /dashboard
- /profiles
- /profiles/{id} (manual correction screen)
- /missions

## Admin JWT session (UI)

Les actions mutatives backend sont protegees par JWT admin.

Dans l'UI, un panneau Session admin est disponible sur:
- /missions
- /missions/{id}
- /profiles/{id}

Workflow:
1. se connecter via username/password admin
2. le token JWT est stocke en localStorage
3. les appels mutatifs envoient automatiquement Authorization: Bearer <token>

## Quality checks

```bash
npm run lint
npx tsc --noEmit
npm run build
```

## Vercel setup (production)

1. Link the project locally (one-time)

```bash
npx vercel link
```

2. Set frontend runtime variable in Vercel project settings

- NEXT_PUBLIC_API_URL=https://your-backend-public-url/api

3. Configure GitHub secrets

- VERCEL_TOKEN
- VERCEL_ORG_ID
- VERCEL_PROJECT_ID

4. Push to main

The workflow [.github/workflows/vercel-deploy.yml](../.github/workflows/vercel-deploy.yml) will:
- pull production environment from Vercel
- build artifacts
- deploy prebuilt assets to production
