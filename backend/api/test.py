"""Minimal Vercel test endpoint."""

from fastapi import FastAPI

app = FastAPI()

@app.get("/test/ping")
def ping():
    return {"status": "ok", "message": "pong"}