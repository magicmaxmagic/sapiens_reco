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

### IMPORTANT: Environment Variables

The `APP_LOGIN_SESSION_SECRET` environment variable **MUST** be set in Vercel before deployment. Without it, the app will show a configuration error page and be inaccessible.

### Local Setup

1. Copy environment file:
```bash
cp .env.example .env.local
```

2. Generate a secure session secret:
```bash
openssl rand -base64 48
```

3. Set the secret in `.env.local`:
```
APP_LOGIN_SESSION_SECRET=<your-generated-secret>
```

### Vercel Project Setup

1. Link the project locally (one-time):

```bash
npx vercel link
```

2. **Set required environment variables in Vercel dashboard** (Project Settings → Environment Variables):

   | Variable | Description | Required |
   |----------|-------------|----------|
   | `NEXT_PUBLIC_API_URL` | Backend API URL (e.g., `https://api.example.com/api`) | Yes |
   | `APP_LOGIN_SESSION_SECRET` | Secure random string for session signing (min 32 chars) | **Yes** |
   | `APP_LOGIN_SESSION_MAX_AGE_SECONDS` | Session duration in seconds (default: 3600) | No |
   | `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | No |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key | No |

3. Configure GitHub secrets (repository Settings → Secrets and variables → Actions):

   - `VERCEL_TOKEN` - Vercel API token
   - `VERCEL_ORG_ID` - Vercel team/org ID
   - `VERCEL_PROJECT_ID` - Vercel project ID

4. Deploy:

   - Push to `uat` branch: triggers preview deploy
   - Push to `main` branch: triggers production deploy
