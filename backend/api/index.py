"""Minimal diagnostic for Vercel debugging."""
import os

# Print environment for debugging
print(f"APP_ENV: {os.environ.get('APP_ENV', 'NOT_SET')}")
print(f"DATABASE_URL: {'SET' if os.environ.get('DATABASE_URL') else 'NOT_SET'}")
print(f"ADMIN_PASSWORD: {'SET' if os.environ.get('ADMIN_PASSWORD') else 'NOT_SET'}")
print(f"JWT_SECRET_KEY: {'SET' if os.environ.get('JWT_SECRET_KEY') else 'NOT_SET'}")

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Optimus API - Diagnostic")

@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})

@app.get("/env")
def env_check():
    return JSONResponse({
        "app_env": os.environ.get("APP_ENV", "NOT_SET"),
        "database_url": "SET" if os.environ.get("DATABASE_URL") else "NOT_SET",
        "admin_password": "SET" if os.environ.get("ADMIN_PASSWORD") else "NOT_SET",
        "jwt_secret": "SET" if os.environ.get("JWT_SECRET_KEY") else "NOT_SET",
        "auth_required": os.environ.get("AUTH_REQUIRED", "NOT_SET"),
    })

# Vercel handler
handler = app