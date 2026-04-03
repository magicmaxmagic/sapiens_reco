"""Vercel serverless entry point."""

from app.main import app

# Vercel expects a top-level `app`, `application`, or `handler`
# This file exports the FastAPI app from app/main.py