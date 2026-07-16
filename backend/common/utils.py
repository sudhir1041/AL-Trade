"""
common/utils.py
---------------
Shared utility functions for TradeMind AI backend.
"""

import math
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


# =============================================================================
# UUID / ID helpers
# =============================================================================

def generate_uuid() -> uuid.UUID:
    """Return a new random UUID v4."""
    return uuid.uuid4()


def generate_uuid_str() -> str:
    """Return a new random UUID v4 as a lowercase hyphenated string."""
    return str(uuid.uuid4())


def is_valid_uuid(value: Any) -> bool:
    """Return True if *value* is a valid UUID string or UUID object."""
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError):
        return False


# =============================================================================
# Encryption (Fernet / AES-128 in CBC with HMAC-SHA256)
# =============================================================================

def encrypt_secret(value: str, key: str) -> str:
    """
    Encrypt *value* using Fernet symmetric encryption.

    Parameters
    ----------
    value : str   Plaintext to encrypt (e.g. an exchange API secret)
    key   : str   URL-safe base64-encoded 32-byte key
                  Generate with: Fernet.generate_key().decode()

    Returns
    -------
    str   Encrypted token (URL-safe base64)

    Raises
    ------
    ValueError   If *key* is empty or invalid
    """
    if not key:
        raise ValueError("ENCRYPTION_KEY must be set before encrypting secrets.")
    if not value:
        return ""

    f = Fernet(key.encode() if isinstance(key, str) else key)
    return f.encrypt(value.encode()).decode()


def decrypt_secret(token: str, key: str) -> str:
    """
    Decrypt a Fernet-encrypted *token*.

    Parameters
    ----------
    token : str   Encrypted token returned by :func:`encrypt_secret`
    key   : str   Encryption key (same as used for encryption)

    Returns
    -------
    str   Decrypted plaintext

    Raises
    ------
    ValueError       If *key* is empty
    InvalidToken     If the token is tampered or the key is wrong
    """
    if not key:
        raise ValueError("ENCRYPTION_KEY must be set before decrypting secrets.")
    if not token:
        return ""

    f = Fernet(key.encode() if isinstance(key, str) else key)
    try:
        return f.decrypt(token.encode()).decode()
    except InvalidToken:
        raise InvalidToken("Could not decrypt secret — token may be tampered or key may be wrong.")


def mask_secret(value: str, visible_chars: int = 4) -> str:
    """
    Return a masked version of *value* showing only the last *visible_chars* characters.

    Example
    -------
    >>> mask_secret("abcdefghijklmno")
    '***********lmno'
    """
    if not value:
        return ""
    if len(value) <= visible_chars:
        return "*" * len(value)
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]


# =============================================================================
# Token generation
# =============================================================================

def generate_secure_token(length: int = 64) -> str:
    """Return a URL-safe cryptographically secure random token of *length* bytes."""
    return secrets.token_urlsafe(length)


def generate_numeric_otp(digits: int = 6) -> str:
    """Return a zero-padded numeric OTP of *digits* digits."""
    max_value = 10 ** digits
    return str(secrets.randbelow(max_value)).zfill(digits)


# =============================================================================
# Timestamp helpers
# =============================================================================

def get_current_timestamp() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


def timestamp_to_ms(dt: datetime) -> int:
    """Convert a datetime to Unix milliseconds."""
    return int(dt.timestamp() * 1000)


def ms_to_timestamp(ms: int) -> datetime:
    """Convert Unix milliseconds to a timezone-aware UTC datetime."""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


# =============================================================================
# Pagination
# =============================================================================

def paginate_queryset(
    queryset: Any,
    page: int,
    page_size: int,
    max_page_size: int = 200,
) -> dict:
    """
    Slice a Django queryset and return pagination metadata.

    Parameters
    ----------
    queryset     : QuerySet   The full (unsliced) queryset
    page         : int        1-based page number
    page_size    : int        Items per page
    max_page_size: int        Hard cap to prevent abuse

    Returns
    -------
    dict with keys:
        results      : list   Current page items (as a queryset slice)
        count        : int    Total number of items
        total_pages  : int    Number of pages
        current_page : int    Current page (1-based)
        has_next     : bool
        has_previous : bool
    """
    page      = max(1, int(page))
    page_size = min(int(page_size), max_page_size)
    page_size = max(1, page_size)

    total_count = queryset.count()
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    start = (page - 1) * page_size
    end   = start + page_size

    return {
        "results":      queryset[start:end],
        "count":        total_count,
        "total_pages":  total_pages,
        "current_page": page,
        "has_next":     page < total_pages,
        "has_previous": page > 1,
    }


# =============================================================================
# Number / financial helpers
# =============================================================================

def round_to_step(value: float, step: float) -> float:
    """
    Round *value* down to the nearest multiple of *step*.
    Used to align order quantities / prices with exchange precision.

    Example
    -------
    >>> round_to_step(1.2345, 0.001)
    1.234
    """
    if step <= 0:
        return value
    precision = max(0, -int(math.floor(math.log10(step))))
    return round(math.floor(value / step) * step, precision)


def calculate_pnl(
    entry_price: float,
    exit_price: float,
    quantity: float,
    side: str,  # "LONG" or "SHORT"
) -> float:
    """
    Calculate realised PnL for a closed position.

    Parameters
    ----------
    entry_price : float   Average entry price
    exit_price  : float   Exit price
    quantity    : float   Position size (in base asset)
    side        : str     "LONG" or "SHORT"

    Returns
    -------
    float   PnL in quote asset (positive = profit, negative = loss)
    """
    if side.upper() == "LONG":
        return (exit_price - entry_price) * quantity
    elif side.upper() == "SHORT":
        return (entry_price - exit_price) * quantity
    raise ValueError(f"Unknown side: {side}. Must be 'LONG' or 'SHORT'.")


def calculate_pnl_pct(entry_price: float, exit_price: float, side: str) -> float:
    """Return the PnL percentage relative to entry price."""
    if entry_price == 0:
        return 0.0
    if side.upper() == "LONG":
        return ((exit_price - entry_price) / entry_price) * 100
    elif side.upper() == "SHORT":
        return ((entry_price - exit_price) / entry_price) * 100
    raise ValueError(f"Unknown side: {side}.")


def calculate_position_size(
    account_balance: float,
    risk_pct: float,
    entry_price: float,
    stop_loss_price: float,
) -> float:
    """
    Calculate position size based on fixed-risk percentage.

    Parameters
    ----------
    account_balance : float   Total account value in quote asset
    risk_pct        : float   Maximum risk as % of balance (e.g. 1.0 = 1%)
    entry_price     : float   Planned entry price
    stop_loss_price : float   Stop-loss price

    Returns
    -------
    float   Position size in base asset (quantity to buy/sell)
    """
    if entry_price <= 0 or stop_loss_price <= 0:
        return 0.0

    risk_amount   = account_balance * (risk_pct / 100)
    price_risk    = abs(entry_price - stop_loss_price)
    if price_risk == 0:
        return 0.0

    return risk_amount / price_risk


# =============================================================================
# String helpers
# =============================================================================

def truncate(text: str, max_length: int = 100, suffix: str = "…") -> str:
    """Truncate *text* to *max_length* characters, appending *suffix* if cut."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def safe_decimal(value: Any, default: float = 0.0) -> float:
    """Safely convert *value* to float, returning *default* on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
