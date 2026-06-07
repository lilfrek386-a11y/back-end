__all__ = ["user_router", "health_router", "auth_router"]

from .user import router as user_router
from .health import router as health_router
from .auth import router as auth_router
