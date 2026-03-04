"""Base login interface."""

import requests
from abc import ABC, abstractmethod


class BaseLogin(ABC):
    """Abstract base class for all login strategies."""

    @abstractmethod
    def authenticate(self, session: requests.Session, base_url: str) -> str:
        """Perform login.

        Args:
            session: requests.Session to attach cookies/headers to.
            base_url: TronClass instance base URL.

        Returns:
            X-SESSION-ID header value.
        """


class TokenLogin(BaseLogin):
    """Login directly with a pre-obtained access token (JWT/Bearer).

    Useful for institutions that provide token-based SSO,
    or when you already hold a valid access token.

    Example::

        login = TokenLogin("eyJhbGci...your_jwt_token")
        client = TronClassClient("https://yourschool.tronclass.com", login)
    """

    def __init__(self, access_token: str, org_id: int = 1):
        self.access_token = access_token
        self.org_id = org_id

    def authenticate(self, session: requests.Session, base_url: str) -> str:
        resp = session.post(
            f"{base_url}/api/login?login=access_token",
            json={"access_token": self.access_token, "org_id": self.org_id},
        )
        resp.raise_for_status()
        profile = session.get(f"{base_url}/api/profile")
        profile.raise_for_status()
        return profile.headers.get("X-SESSION-ID", "")
