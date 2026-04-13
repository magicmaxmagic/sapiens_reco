"""Minimal test endpoint to diagnose issues."""

def handler(request):
    return {
        "statusCode": 200,
        "body": '{"status": "ok", "message": "Test endpoint working"}',
        "headers": {"Content-Type": "application/json"}
    }
