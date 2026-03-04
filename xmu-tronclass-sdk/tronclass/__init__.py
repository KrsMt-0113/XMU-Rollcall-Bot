"""
XMU-Tronclass-SDK
~~~~~~~~~~~~~~~~~

Python SDK for TronClass LMS.

Basic usage::

    from tronclass import TronClassClient
    from tronclass.auth import XMULogin

    login = XMULogin("your_username", "your_password")
    client = TronClassClient("https://lnt.xmu.edu.cn", login)

    courses = client.courses.list()
    rollcalls = client.rollcall.get_active()
"""

from .client import TronClassClient
from .exceptions import (
    TronClassError,
    AuthError,
    NotFoundError,
    PermissionError,
    RollcallError,
)

__all__ = [
    "TronClassClient",
    "TronClassError",
    "AuthError",
    "NotFoundError",
    "PermissionError",
    "RollcallError",
]

__version__ = "0.1.0"
