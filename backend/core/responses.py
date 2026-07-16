"""
core/responses.py
-----------------
Standardised API response helpers for TradeMind AI.

Every response follows the envelope:

    Success:
        {
            "success": true,
            "message": "Operation completed.",
            "data":    { ... },
            "meta":    { "page": 1, "total": 100, ... }
        }

    Error:
        {
            "success": false,
            "error": {
                "code":    "VALIDATION_ERROR",
                "message": "...",
                "details": {}
            }
        }
"""

from typing import Any

from rest_framework import status
from rest_framework.response import Response


# =============================================================================
# Success responses
# =============================================================================

def success_response(
    data: Any = None,
    message: str = "Operation completed.",
    meta: dict | None = None,
    status_code: int = status.HTTP_200_OK,
) -> Response:
    """
    Return a standard success response.

    Parameters
    ----------
    data        : Any        Serialised payload (dict, list, or None)
    message     : str        Human-readable success message
    meta        : dict       Pagination / extra metadata
    status_code : int        HTTP status code (default 200)

    Example
    -------
    >>> return success_response(
    ...     data={"order_id": "abc"},
    ...     message="Order placed successfully.",
    ...     status_code=201,
    ... )
    """
    return Response(
        {
            "success": True,
            "message": message,
            "data":    data if data is not None else {},
            "meta":    meta or {},
        },
        status=status_code,
    )


def created_response(
    data: Any = None,
    message: str = "Resource created successfully.",
    meta: dict | None = None,
) -> Response:
    """Shortcut for HTTP 201 Created responses."""
    return success_response(data=data, message=message, meta=meta, status_code=status.HTTP_201_CREATED)


def no_content_response(message: str = "Resource deleted.") -> Response:
    """Shortcut for HTTP 204 No Content responses."""
    return Response(
        {"success": True, "message": message},
        status=status.HTTP_204_NO_CONTENT,
    )


def paginated_response(
    data: list,
    page: int,
    page_size: int,
    total_count: int,
    message: str = "Data retrieved successfully.",
    extra_meta: dict | None = None,
) -> Response:
    """
    Return a paginated success response with standard meta fields.

    Parameters
    ----------
    data        : list   Current page's serialised items
    page        : int    Current page number (1-based)
    page_size   : int    Number of items per page
    total_count : int    Total items across all pages
    """
    import math
    total_pages = math.ceil(total_count / page_size) if page_size > 0 else 0

    meta = {
        "page":        page,
        "page_size":   page_size,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_next":    page < total_pages,
        "has_previous": page > 1,
    }
    if extra_meta:
        meta.update(extra_meta)

    return success_response(data=data, message=message, meta=meta)


# =============================================================================
# Error responses
# =============================================================================

def error_response(
    code: str,
    message: str,
    details: dict | None = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    """
    Return a standard error response.

    Parameters
    ----------
    code        : str    Machine-readable error code (e.g. "VALIDATION_ERROR")
    message     : str    Human-readable error message
    details     : dict   Optional extra context (field errors, rule names, etc.)
    status_code : int    HTTP status code (default 400)

    Example
    -------
    >>> return error_response(
    ...     code="INVALID_CREDENTIALS",
    ...     message="Email or password is incorrect.",
    ...     status_code=401,
    ... )
    """
    return Response(
        {
            "success": False,
            "error": {
                "code":    code,
                "message": message,
                "details": details or {},
            },
        },
        status=status_code,
    )


def validation_error_response(
    message: str = "Validation failed.",
    field_errors: dict | None = None,
) -> Response:
    """Shortcut for 400 validation errors with optional per-field error map."""
    return error_response(
        code="VALIDATION_ERROR",
        message=message,
        details={"field_errors": field_errors} if field_errors else {},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def not_found_response(resource: str = "Resource") -> Response:
    """Shortcut for 404 responses."""
    return error_response(
        code="RESOURCE_NOT_FOUND",
        message=f"{resource} not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def unauthorized_response(message: str = "Authentication required.") -> Response:
    """Shortcut for 401 responses."""
    return error_response(
        code="AUTHENTICATION_REQUIRED",
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


def forbidden_response(message: str = "Permission denied.") -> Response:
    """Shortcut for 403 responses."""
    return error_response(
        code="AUTHORIZATION_DENIED",
        message=message,
        status_code=status.HTTP_403_FORBIDDEN,
    )


def rate_limit_response(retry_after: int | None = None) -> Response:
    """Shortcut for 429 rate limit responses."""
    details = {"retry_after_seconds": retry_after} if retry_after else {}
    return error_response(
        code="RATE_LIMIT_EXCEEDED",
        message="Too many requests. Please slow down and try again.",
        details=details,
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )


def server_error_response(message: str = "An unexpected error occurred.") -> Response:
    """Shortcut for 500 responses."""
    return error_response(
        code="INTERNAL_SERVER_ERROR",
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
