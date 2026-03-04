"""Profile and user settings API."""

from typing import List, Optional
from . import APINamespace
from ..models import User


class ProfileAPI(APINamespace):
    """User profile and account settings.

    Access via ``client.profile``.
    """

    def me(self) -> User:
        """Return the currently logged-in user's profile.

        Returns:
            :class:`~tronclass.models.User`
        """
        d = self._get("/api/profile")
        return User(
            id=d["id"],
            name=d.get("name", ""),
            email=d.get("email"),
            avatar=d.get("avatar"),
            role=d.get("role"),
            raw=d,
        )

    def update_name(self, name: str) -> dict:
        """Change display name."""
        return self._put("/api/user/name", json={"name": name})

    def update_email(self, email: str) -> dict:
        """Update email address."""
        return self._put("/api/user/email", json={"email": email})

    def update_mobile(self, mobile: str) -> dict:
        """Update mobile phone number."""
        return self._put("/api/user/mobile-phone", json={"mobile_phone": mobile})

    def update_password(self, old_password: str, new_password: str) -> dict:
        """Change account password."""
        return self._put(
            "/api/user/password",
            json={"old_password": old_password, "password": new_password},
        )

    def update_avatar(self, image_path: str) -> dict:
        """Upload a new avatar image.

        Args:
            image_path: Local path to image file.
        """
        with open(image_path, "rb") as f:
            return self._post("/api/user/avatar", files={"file": f})

    def get_tags(self) -> dict:
        """Return OneSignal push notification tags and alias.

        Returns:
            dict with keys ``alias`` (str) and ``tags`` (list of str).
        """
        return self._get("/api/user/tags")

    def get_notification_settings(self) -> dict:
        """Return notification preference settings."""
        return self._get("/api/user/ntf-setting")

    def update_notification_settings(self, settings: dict) -> dict:
        """Update notification preferences.

        Args:
            settings: dict of notification settings (e.g. ``{"rollcall": True}``).
        """
        return self._put("/api/user/ntf-setting", json=settings)

    def get_bound_services(self) -> dict:
        """Return third-party accounts bound to this user (WeChat, LINE, etc.)."""
        return self._get("/api/user/bound-services")

    def get_recently_visited_courses(self) -> List[dict]:
        """Return recently visited courses."""
        return self._get("/api/user/recently-visited-courses")

    def get_uploads(self) -> List[dict]:
        """Return user's uploaded files."""
        return self._get("/api/user/uploads")

    def get_health_passport(self) -> dict:
        """Return health passport info (institution-specific)."""
        return self._get("/api/user/health-passport")
