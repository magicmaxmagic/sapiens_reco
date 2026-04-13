"""Minimal Vercel entry point for debugging."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os

app = FastAPI(title="Optimus API Debug")

# Basic health check
@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})

# Debug endpoint
@app.get("/debug/env")
def debug_env():
    return JSONResponse({
        "app_env": os.environ.get("APP_ENV", "NOT_SET"),
        "auth_required": os.environ.get("AUTH_REQUIRED", "NOT_SET"),
        "admin_password": "***SET***" if os.environ.get("ADMIN_PASSWORD") else "***NOT_SET***",
        "jwt_secret": "***SET***" if os.environ.get("JWT_SECRET_KEY") else "***NOT_SET***",
        "database_url": "***SET***" if os.environ.get("DATABASE_URL") else "***NOT_SET***",
    })

# Vercel handler
handler = app