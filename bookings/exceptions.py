import logging

from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Wraps DRF's default exception handler so framework-raised errors
    (404s, permission errors, unhandled exceptions) follow a consistent
    shape: {"error": {"detail": ..., "status_code": ...}}.
    """
    response = exception_handler(exc, context)

    if response is not None:
        view = context.get("view")
        logger.warning(
            "API error in %s: %s",
            view.__class__.__name__ if view else "unknown view",
            exc,
        )
        response.data = {
            "error": {
                "detail": response.data,
                "status_code": response.status_code,
            }
        }

    return response