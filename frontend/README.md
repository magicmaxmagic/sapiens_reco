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
- APP_LOGIN_SESSION_SECRET=<random-long-secret>
- NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
- NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

Optional variable:
- APP_LOGIN_SESSION_MAX_AGE_SECONDS=3600

## Main pages

- /dashboard
- /profiles
- /profiles/{id} (manual correction screen)
- /missions
- /notes (lecture table notes via Supabase)

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

## Login global applicatif

L'app frontend est maintenant protegee par un login global (/login) base sur une session cookie signee.

Fonctionnement:
1. l'utilisateur se connecte via /login avec l'identifiant admin backend
2. le frontend verifie les credentials via POST /auth/login backend
3. un cookie de session signe est pose pour autoriser l'acces aux pages
4. sans session valide, middleware redirige vers /login

Notes:
- la verification du login utilise les variables backend ADMIN_USERNAME/ADMIN_PASSWORD
- APP_LOGIN_SESSION_SECRET est obligatoire pour activer la protection globale
- si APP_LOGIN_SESSION_SECRET est absent, l'app redirige vers /setup-error

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
- APP_LOGIN_SESSION_SECRET=<random-long-secret>
- APP_LOGIN_SESSION_MAX_AGE_SECONDS=3600 (optional)
- NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
- NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

3. Configure GitHub secrets

- VERCEL_TOKEN
- VERCEL_ORG_ID
- VERCEL_PROJECT_ID

4. Push strategy

- Push on uat (or open PR): triggers preview deploy via [../.github/workflows/vercel-preview.yml](../.github/workflows/vercel-preview.yml)
- Push on main: triggers production deploy via [../.github/workflows/vercel-deploy.yml](../.github/workflows/vercel-deploy.yml)

Production workflow does:
- npm ci
- lint + typecheck
- vercel pull (production)
- vercel build --prod
- vercel deploy --prebuilt --prod
