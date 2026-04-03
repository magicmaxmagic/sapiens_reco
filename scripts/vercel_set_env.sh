#!/usr/bin/env bash
set -euo pipefail

# vercel_set_env.sh
# Usage:
#   export VERCEL_TOKEN=... \
#   export VERCEL_PROJECT_ID=... \
#   bash scripts/vercel_set_env.sh [--api-url "https://your-backend/api"]
# Or pass --token and --project flags.

print_usage() {
  cat <<'USAGE'
Usage: vercel_set_env.sh [--token <vercel_token>] [--project <project_id>] [--api-url <url>] [--yes]

Pre-reqs:
 - curl, python3
 - VERCEL_TOKEN (or pass --token)
 - VERCEL_PROJECT_ID (or pass --project)

This script will create or update the following env vars on Vercel (target=production):
 - APP_LOGIN_SESSION_SECRET
 - NEXT_PUBLIC_API_URL

If a local file frontend/.env.local exists, values are read from it by default.
USAGE
}

# defaults
VERCEL_TOKEN=${VERCEL_TOKEN:-}
VERCEL_PROJECT_ID=${VERCEL_PROJECT_ID:-}
API_URL=""
ASSUME_YES=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --token) VERCEL_TOKEN="$2"; shift 2;;
    --project) VERCEL_PROJECT_ID="$2"; shift 2;;
    --api-url) API_URL="$2"; shift 2;;
    --yes) ASSUME_YES=1; shift 1;;
    -h|--help) print_usage; exit 0;;
    *) echo "Unknown arg: $1"; print_usage; exit 1;;
  esac
done

if [ -z "${VERCEL_TOKEN:-}" ]; then
  echo "ERROR: VERCEL_TOKEN not set. Export it or pass --token." >&2
  exit 1
fi
if [ -z "${VERCEL_PROJECT_ID:-}" ]; then
  echo "ERROR: VERCEL_PROJECT_ID not set. Export it or pass --project." >&2
  exit 1
fi

# read from frontend/.env.local if present
if [ -f frontend/.env.local ]; then
  echo "Reading frontend/.env.local for defaults..."
  # shellcheck disable=SC2002
  SECRET=$(grep -E '^APP_LOGIN_SESSION_SECRET=' frontend/.env.local || true)
  API_URL_LOCAL=$(grep -E '^NEXT_PUBLIC_API_URL=' frontend/.env.local || true)
  if [ -n "$SECRET" ]; then
    SECRET=${SECRET#APP_LOGIN_SESSION_SECRET=}
  else
    SECRET=""
  fi
  if [ -n "$API_URL_LOCAL" ]; then
    API_URL_LOCAL=${API_URL_LOCAL#NEXT_PUBLIC_API_URL=}
  else
    API_URL_LOCAL=""
  fi
else
  SECRET=""
  API_URL_LOCAL=""
fi

# prefer explicit --api-url, then local .env, else empty
if [ -n "$API_URL" ]; then
  FINAL_API_URL="$API_URL"
else
  FINAL_API_URL="$API_URL_LOCAL"
fi

# generate secret if missing
if [ -z "$SECRET" ]; then
  echo "Generating new APP_LOGIN_SESSION_SECRET..."
  SECRET=$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)
fi

if [ -z "$FINAL_API_URL" ]; then
  echo "WARNING: NEXT_PUBLIC_API_URL not set. Provide --api-url or set it in frontend/.env.local." >&2
  read -r -p "Continue without NEXT_PUBLIC_API_URL? (y/N): " resp
  if [[ ! "$resp" =~ ^[Yy]$ ]]; then
    echo "Aborting."; exit 1
  fi
fi

if [ "$ASSUME_YES" -ne 1 ]; then
  echo "About to create/update on Vercel project: $VERCEL_PROJECT_ID"
  echo "APP_LOGIN_SESSION_SECRET will be set (hidden)."
  echo "NEXT_PUBLIC_API_URL will be set to: ${FINAL_API_URL:-<empty>}"
  read -r -p "Proceed? (y/N): " resp
  if [[ ! "$resp" =~ ^[Yy]$ ]]; then
    echo "Aborting."; exit 1
  fi
fi

# helper to find env id by key
get_env_id() {
  local key="$1"
  local res
  res=$(curl -s -H "Authorization: Bearer ${VERCEL_TOKEN}" \
    "https://api.vercel.com/v9/projects/${VERCEL_PROJECT_ID}/env") || return 1
  python3 - <<PY "$key"
import json,sys
key=sys.argv[1]
try:
    data=json.load(sys.stdin)
except Exception:
    sys.exit(0)
for k in data.get('envs', []) + data.get('env', []):
    if k.get('key')==key:
        print(k.get('id'))
        sys.exit(0)
sys.exit(0)
PY
}

set_or_update_env() {
  local key="$1"
  local value="$2"
  local env_id
  env_id=$(get_env_id "$key" | tr -d '\n') || true

  if [ -n "$env_id" ]; then
    echo "Updating existing env var '$key' (id=$env_id)"
    export VALUE="$value"
    payload=$(python3 - <<'PY'
import os,json
print(json.dumps({"value": os.environ.get('VALUE','')}))
PY
)
    curl -s -X PATCH \
      -H "Authorization: Bearer ${VERCEL_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "$payload" \
      "https://api.vercel.com/v9/projects/${VERCEL_PROJECT_ID}/env/$env_id"
    echo "\nUpdated $key"
  else
    echo "Creating env var '$key' (target=production)"
    export KEY="$key"
    export VALUE="$value"
    payload=$(python3 - <<'PY'
import os,json
print(json.dumps({"key": os.environ.get('KEY',''), "value": os.environ.get('VALUE',''), "target": ["production"], "type": "encrypted"}))
PY
)
    curl -s -X POST \
      -H "Authorization: Bearer ${VERCEL_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "$payload" \
      "https://api.vercel.com/v9/projects/${VERCEL_PROJECT_ID}/env"
    echo "\nCreated $key"
  fi
}

# perform actions
set_or_update_env "APP_LOGIN_SESSION_SECRET" "$SECRET"
if [ -n "${FINAL_API_URL}" ]; then
  set_or_update_env "NEXT_PUBLIC_API_URL" "$FINAL_API_URL"
fi

echo "Done. Remember to trigger a redeploy if needed (push or re-deploy in Vercel UI)."

echo "If you want me to print the generated secret, run: echo \"$SECRET\""

echo "Script finished." 
