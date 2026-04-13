# Test endpoint for Vercel Python runtime
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/ping")
def ping():
    return JSONResponse({"status": "ok", "message": "pong"})

# Vercel handler
handler = app