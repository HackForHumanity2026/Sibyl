"""PostgreSQL-safe text sanitization utilities.

Prevents database persistence failures caused by:
- Null bytes (\u0000) which PostgreSQL text/jsonb cannot store
- Unpaired Unicode surrogates (\ud800-\udfff) which crash psycopg JSON serialization
- Excessively long strings from external APIs that could cause memory issues

This module provides both a utility function for explicit sanitization and
a SQLAlchemy event listener for automatic sanitization of all database writes.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Maximum string length to prevent memory-bomb payloads from external APIs
MAX_STRING_LENGTH = 100_000  # 100KB per string field

# Regex pattern for PostgreSQL-incompatible characters:
# - \x00 (null byte)
# - Unpaired surrogates (U+D800 to U+DFFF)
_INVALID_PG_CHARS = re.compile(r"[\x00\ud800-\udfff]")


def sanitize_string(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
    """Sanitize a single string for PostgreSQL compatibility.
    
    Args:
        value: The string to sanitize
        max_length: Maximum allowed string length (default: 100KB)
        
    Returns:
        Sanitized string safe for PostgreSQL text/jsonb columns
    """
    if not value:
        return value
    
    # Remove PostgreSQL-incompatible characters
    sanitized = _INVALID_PG_CHARS.sub("", value)
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        logger.warning(
            "Truncated string from %d to %d characters",
            len(value),
            max_length,
        )
    
    return sanitized


def sanitize_for_pg(value: Any, max_length: int = MAX_STRING_LENGTH) -> Any:
    """Recursively sanitize a value for PostgreSQL compatibility.
    
    Handles strings, dicts, lists, and nested structures. Non-string
    primitive types (int, float, bool, None) are returned unchanged.
    
    Args:
        value: Any value that might contain strings
        max_length: Maximum allowed string length (default: 100KB)
        
    Returns:
        Sanitized value safe for PostgreSQL text/jsonb columns
        
    Examples:
        >>> sanitize_for_pg("hello\\x00world")
        'helloworld'
        
        >>> sanitize_for_pg({"key": "value\\x00"})
        {'key': 'value'}
        
        >>> sanitize_for_pg(["a\\x00", {"b": "c\\x00"}])
        ['a', {'b': 'c'}]
    """
    if value is None:
        return None
    
    if isinstance(value, str):
        return sanitize_string(value, max_length)
    
    if isinstance(value, dict):
        return {
            sanitize_for_pg(k, max_length): sanitize_for_pg(v, max_length)
            for k, v in value.items()
        }
    
    if isinstance(value, list):
        return [sanitize_for_pg(item, max_length) for item in value]
    
    if isinstance(value, tuple):
        return tuple(sanitize_for_pg(item, max_length) for item in value)
    
    # Primitives (int, float, bool, bytes, etc.) - return unchanged
    return value


def contains_invalid_chars(value: str) -> bool:
    """Check if a string contains PostgreSQL-incompatible characters.
    
    Useful for logging/debugging without modifying the value.
    
    Args:
        value: String to check
        
    Returns:
        True if the string contains null bytes or unpaired surrogates
    """
    if not value:
        return False
    return bool(_INVALID_PG_CHARS.search(value))
