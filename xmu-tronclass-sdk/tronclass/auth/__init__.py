"""Auth module — login strategies."""
from .xmu import XMULogin
from .base import BaseLogin, TokenLogin

__all__ = ["XMULogin", "TokenLogin", "BaseLogin"]
