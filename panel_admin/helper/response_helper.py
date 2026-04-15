from django.http import JsonResponse


def json_response(payload, status=200):
    """Reusable stateless JSON response helper for custom payload structures."""
    return JsonResponse(payload, status=status)


def success_response(message="Success", data=None, status=200):
    """Reusable stateless helper for consistent success responses."""
    payload = {
        "success": True,
        "message": message,
        "data": data,
    }
    return JsonResponse(payload, status=status)


def error_response(message="Error", errors=None, status=400):
    """Reusable stateless helper for consistent error responses."""
    payload = {
        "success": False,
        "message": message,
        "errors": errors,
    }
    return JsonResponse(payload, status=status)
