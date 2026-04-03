import traceback

try:
    from app.main import app  # attempt to import the real FastAPI app
except Exception:  # pragma: no cover - debug fallback for serverless
    tb = traceback.format_exc()

    def _get_error_info() -> dict:
        # Return the import traceback to help debugging serverless startup failures
        return {"status": "error", "trace": tb}

    from fastapi import FastAPI

    app = FastAPI()

    @app.get("/api/health")
    def health_debug():
        return _get_error_info()