"""Rate limiter instance — shared across all route modules.

Set ``DISABLE_RATE_LIMIT=1`` env var to disable (used in tests).
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import RATE_LIMIT_DEFAULT


class _NoopLimiter:
    """Drop-in replacement that applies no limits."""

    def limit(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator


if os.getenv("DISABLE_RATE_LIMIT"):
    limiter = _NoopLimiter()
else:
    limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT_DEFAULT])
