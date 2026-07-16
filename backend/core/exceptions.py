"""
core/exceptions.py
------------------
Custom exception hierarchy + DRF exception handler for TradeMind AI.
All API errors return a consistent JSON envelope:

    {
        "success": false,
        "error": {
            "code":    "RISK_LIMIT_EXCEEDED",
            "message": "Daily loss limit reached.",
            "details": {}   # optional extra context
        }
    }
"""

import logging
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied as DRFPermissionDenied,
    Throttled,
    ValidationError as DRFValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("trademind.exceptions")


# =============================================================================
# Base exception
# =============================================================================

class TradeMindBaseException(APIException):
    """
    Root exception for all TradeMind AI business errors.

    Attributes
    ----------
    status_code : int          HTTP status to return
    error_code  : str          Machine-readable error identifier
    default_detail : str       Human-readable message
    details     : dict         Optional structured extra context
    """

    status_code   = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code    = "INTERNAL_ERROR"
    default_detail = "An unexpected error occurred."

    def __init__(
        self,
        detail: str | None = None,
        details: dict | None = None,
        error_code: str | None = None,
    ) -> None:
        self.detail   = detail or self.default_detail
        self.details  = details or {}
        if error_code:
            self.error_code = error_code
        super().__init__(detail=self.detail)


# =============================================================================
# Specific exceptions
# =============================================================================

class ValidationException(TradeMindBaseException):
    """Raised when user-supplied input fails validation."""
    status_code    = status.HTTP_400_BAD_REQUEST
    error_code     = "VALIDATION_ERROR"
    default_detail = "Input validation failed."


class AuthenticationException(TradeMindBaseException):
    """Raised when authentication credentials are missing or invalid."""
    status_code    = status.HTTP_401_UNAUTHORIZED
    error_code     = "AUTHENTICATION_FAILED"
    default_detail = "Authentication credentials are invalid or missing."


class AuthorizationException(TradeMindBaseException):
    """Raised when an authenticated user lacks the required permissions."""
    status_code    = status.HTTP_403_FORBIDDEN
    error_code     = "AUTHORIZATION_DENIED"
    default_detail = "You do not have permission to perform this action."


class ResourceNotFoundException(TradeMindBaseException):
    """Raised when a requested resource cannot be found."""
    status_code    = status.HTTP_404_NOT_FOUND
    error_code     = "RESOURCE_NOT_FOUND"
    default_detail = "The requested resource was not found."


class ExchangeException(TradeMindBaseException):
    """
    Raised when communication with a cryptocurrency exchange fails.

    Parameters
    ----------
    exchange_id : str   Identifier of the exchange that caused the error
    """
    status_code    = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code     = "EXCHANGE_UNAVAILABLE"
    default_detail = "Exchange communication failed."

    def __init__(
        self,
        detail: str | None = None,
        exchange_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        self.exchange_id = exchange_id
        extra = {"exchange_id": exchange_id} if exchange_id else {}
        if details:
            extra.update(details)
        super().__init__(detail=detail, details=extra)


class ExchangeAuthException(ExchangeException):
    """Raised when exchange API authentication fails."""
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code  = "EXCHANGE_AUTH_FAILED"
    default_detail = "Exchange API authentication failed. Check your API credentials."


class ExchangeRateLimitException(ExchangeException):
    """Raised when the exchange rate limit is hit."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code  = "EXCHANGE_RATE_LIMIT"
    default_detail = "Exchange rate limit reached. Request will be retried."


class BusinessLogicException(TradeMindBaseException):
    """Raised when a business rule is violated (not a validation or auth issue)."""
    status_code    = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code     = "BUSINESS_LOGIC_ERROR"
    default_detail = "The operation could not be completed due to a business rule violation."


class InfrastructureException(TradeMindBaseException):
    """Raised when an internal infrastructure component (Redis, DB, queue) fails."""
    status_code    = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code     = "INFRASTRUCTURE_ERROR"
    default_detail = "A required service is temporarily unavailable."


class RateLimitException(TradeMindBaseException):
    """Raised when a user or IP exceeds the configured API rate limits."""
    status_code    = status.HTTP_429_TOO_MANY_REQUESTS
    error_code     = "RATE_LIMIT_EXCEEDED"
    default_detail = "Too many requests. Please slow down and try again."

    def __init__(self, detail: str | None = None, retry_after: int | None = None, **kwargs) -> None:
        self.retry_after = retry_after
        extra = {"retry_after_seconds": retry_after} if retry_after else {}
        super().__init__(detail=detail, details=extra, **kwargs)


class RiskLimitException(TradeMindBaseException):
    """
    Raised when the Risk Engine rejects an order due to a configured limit.

    Parameters
    ----------
    rule_name : str   Name of the violated risk rule
    """
    status_code    = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code     = "RISK_LIMIT_EXCEEDED"
    default_detail = "Order rejected: risk limit exceeded."

    def __init__(
        self,
        detail: str | None = None,
        rule_name: str | None = None,
        details: dict | None = None,
    ) -> None:
        self.rule_name = rule_name
        extra = {"rule_name": rule_name} if rule_name else {}
        if details:
            extra.update(details)
        super().__init__(detail=detail, details=extra)


class OrderRejectedException(TradeMindBaseException):
    """Raised when an order is rejected (by the Risk Engine or the exchange)."""
    status_code    = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code     = "ORDER_REJECTED"
    default_detail = "Order was rejected."


class DuplicateOrderException(OrderRejectedException):
    """Raised when an order with the same idempotency key has already been submitted."""
    error_code     = "DUPLICATE_ORDER"
    default_detail = "Duplicate order detected. Use a unique idempotency key."


class EmergencyStopActiveException(TradeMindBaseException):
    """Raised when an order is attempted while emergency stop is active."""
    status_code    = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code     = "EMERGENCY_STOP_ACTIVE"
    default_detail = "Emergency stop is active. No orders can be placed."


class StrategyNotFoundException(ResourceNotFoundException):
    """Raised when the requested strategy is not found."""
    error_code = "STRATEGY_NOT_FOUND"
    default_detail = "Strategy not found."


class ExchangeAccountNotFoundException(ResourceNotFoundException):
    """Raised when the requested exchange account is not found."""
    error_code = "EXCHANGE_ACCOUNT_NOT_FOUND"
    default_detail = "Exchange account not found."


class InvalidCredentialsException(AuthenticationException):
    """Raised on invalid email/password combinations."""
    error_code     = "INVALID_CREDENTIALS"
    default_detail = "Invalid email or password."


class AccountNotActiveException(AuthenticationException):
    """Raised when a user tries to log in before verifying their email."""
    error_code     = "ACCOUNT_NOT_ACTIVE"
    default_detail = "Account not active. Please verify your email."


class TwoFactorRequiredException(AuthenticationException):
    """Raised when 2FA is enabled but the OTP was not supplied."""
    error_code     = "TWO_FACTOR_REQUIRED"
    default_detail = "Two-factor authentication code required."


class TwoFactorInvalidException(AuthenticationException):
    """Raised when the supplied TOTP/OTP code is wrong."""
    error_code     = "TWO_FACTOR_INVALID"
    default_detail = "Invalid two-factor authentication code."


# =============================================================================
# DRF custom exception handler
# =============================================================================

def custom_exception_handler(exc: Exception, context: Any) -> Response | None:
    """
    Unified DRF exception handler.

    Returns every error — whether raised by TradeMind code or DRF — in the
    standard envelope:

        { "success": false, "error": { "code": "...", "message": "...", "details": {} } }
    """
    # Let DRF translate Django exceptions first (e.g. PermissionDenied → 403)
    response = drf_exception_handler(exc, context)

    request = context.get("request")
    user_id = str(getattr(getattr(request, "user", None), "id", "anonymous"))

    # ── TradeMind custom exceptions ─────────────────────────────────────────
    if isinstance(exc, TradeMindBaseException):
        logger.warning(
            "TradeMind exception: %s — %s",
            exc.error_code,
            exc.detail,
            extra={"user_id": user_id, "error_code": exc.error_code},
        )
        return Response(
            {
                "success": False,
                "error": {
                    "code":    exc.error_code,
                    "message": str(exc.detail),
                    "details": exc.details,
                },
            },
            status=exc.status_code,
        )

    # ── DRF built-in exceptions ─────────────────────────────────────────────
    if response is not None:
        code, message = _extract_drf_error(exc, response)
        logger.warning(
            "DRF exception: %s — %s",
            code,
            message,
            extra={"user_id": user_id},
        )
        response.data = {
            "success": False,
            "error": {
                "code":    code,
                "message": message,
                "details": {},
            },
        }
        return response

    # ── Unhandled server errors ─────────────────────────────────────────────
    logger.exception(
        "Unhandled exception in view",
        exc_info=exc,
        extra={"user_id": user_id},
    )
    return Response(
        {
            "success": False,
            "error": {
                "code":    "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Our team has been notified.",
                "details": {},
            },
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _extract_drf_error(exc: Exception, response: Response) -> tuple[str, str]:
    """Extract a (code, message) tuple from a standard DRF exception."""

    code_map = {
        NotAuthenticated:    ("AUTHENTICATION_REQUIRED",  "Authentication credentials were not provided."),
        AuthenticationFailed:("AUTHENTICATION_FAILED",    "Invalid authentication credentials."),
        DRFPermissionDenied: ("AUTHORIZATION_DENIED",     "You do not have permission to perform this action."),
        PermissionDenied:    ("AUTHORIZATION_DENIED",     "You do not have permission to perform this action."),
        NotFound:            ("RESOURCE_NOT_FOUND",       "The requested resource was not found."),
        Throttled:           ("RATE_LIMIT_EXCEEDED",      "Request was throttled. Try again later."),
        DRFValidationError:  ("VALIDATION_ERROR",         _flatten_validation_errors(response.data)),
        DjangoValidationError:("VALIDATION_ERROR",        "Validation error."),
    }

    for exc_type, (code, msg) in code_map.items():
        if isinstance(exc, exc_type):
            return code, msg

    # Generic fallback
    data = response.data
    if isinstance(data, dict):
        msg = str(data.get("detail", "An error occurred."))
    else:
        msg = str(data)

    return "API_ERROR", msg


def _flatten_validation_errors(data: Any, prefix: str = "") -> str:
    """Flatten nested DRF validation error dicts into a single readable string."""
    messages: list[str] = []

    if isinstance(data, dict):
        for field, errors in data.items():
            key = f"{prefix}{field}" if not prefix else f"{prefix}.{field}"
            messages.append(_flatten_validation_errors(errors, prefix=key))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                messages.append(_flatten_validation_errors(item, prefix=prefix))
            else:
                label = f"{prefix}: " if prefix else ""
                messages.append(f"{label}{item}")
    else:
        label = f"{prefix}: " if prefix else ""
        messages.append(f"{label}{data}")

    return " | ".join(filter(None, messages))
