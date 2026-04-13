"""Vercel serverless entry point."""

# Minimal test first
try:
    from app.main import app
except Exception as e:
    import traceback
    error_msg = traceback.format_exc()
    
    def app(request):
        return {
            "statusCode": 500,
            "body": f'{{"error": "{str(e)}", "traceback": "{error_msg}"}}',
            "headers": {"Content-Type": "application/json"}
        }
