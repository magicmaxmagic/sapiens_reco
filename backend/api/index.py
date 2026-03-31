import traceback

try:
	from app.main import app  # attempt to import the real FastAPI app
except Exception as exc:  # pragma: no cover - debug fallback for serverless
	tb = traceback.format_exc()
	from fastapi import FastAPI

	app = FastAPI()

	@app.get("/api/health")
	def health_debug():
		# Return the import traceback to help debugging serverless startup failures
		return {"status": "error", "error": str(exc), "trace": tb}
