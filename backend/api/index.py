"""Vercel serverless entry point."""
import sys
import traceback

# Try to import and catch any errors
_error_info = None
try:
    from app.main import app
except Exception as e:
    _error_info = {
        "error": str(e),
        "type": type(e).__name__,
        "traceback": traceback.format_exc()
    }
    
    # Create a minimal error app
    from fastapi import FastAPI, Response
    from fastapi.responses import JSONResponse
    
    app = FastAPI()
    
    @app.get("/{path:path}")
    async def error_handler(path: str):
        return JSONResponse(
            status_code=500,
            content=_error_info
        )