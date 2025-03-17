from rest_framework.response import Response
from django.utils.timezone import now

def custom_response(status, message, data=None):
    return Response(
        {
            "status": status,
            "message": message,
            "data": data
        },
        status=status
    )

def error_response(status, error, message, path):
    return Response(
        {
            "timestamp": now().isoformat(),
            "status": status,
            "path": path,
            "error": error,
            "message": message
        },
        status=status
    )
