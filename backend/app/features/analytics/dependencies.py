"""Analytics module dependency re-exports.

Provides a clean, stable import surface for the analytics feature so that
other layers within this module do not need to reach into core or auth.
"""

from app.features.auth.dependencies import RequireRole, get_current_user

__all__ = ["get_current_user", "RequireRole"]
