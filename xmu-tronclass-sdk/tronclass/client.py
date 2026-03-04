"""TronClassClient — main entry point for the SDK."""

import requests
from typing import Optional

from .auth.base import BaseLogin
from .exceptions import TronClassError, AuthError
from .api.profile import ProfileAPI
from .api.courses import CoursesAPI
from .api.rollcall import RollcallAPI
from .api.assignments import AssignmentsAPI
from .api.forum import ForumAPI
from .api.notifications import NotificationsAPI
from .api.activities import ActivitiesAPI

_UA = (
    "Mozilla/5.0 (Linux; Android 6.0; Nexus 5) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/142.0.0.0 Mobile Safari/537.36"
)


class TronClassClient:
    """Main SDK client for TronClass LMS.

    Wraps a :class:`requests.Session` and exposes namespaced API modules.

    Args:
        base_url: Root URL of the TronClass instance, e.g. ``https://lnt.xmu.edu.cn``.
        login: A login strategy instance (:class:`~tronclass.auth.XMULogin`,
               :class:`~tronclass.auth.TokenLogin`, or any :class:`~tronclass.auth.BaseLogin`).

    Attributes:
        profile:       :class:`~tronclass.api.profile.ProfileAPI`
        courses:       :class:`~tronclass.api.courses.CoursesAPI`
        rollcall:      :class:`~tronclass.api.rollcall.RollcallAPI`
        assignments:   :class:`~tronclass.api.assignments.AssignmentsAPI`
        forum:         :class:`~tronclass.api.forum.ForumAPI`
        notifications: :class:`~tronclass.api.notifications.NotificationsAPI`
        activities:    :class:`~tronclass.api.activities.ActivitiesAPI`

    Example::

        from tronclass import TronClassClient
        from tronclass.auth import XMULogin

        client = TronClassClient("https://lnt.xmu.edu.cn", XMULogin("u", "p"))

        me = client.profile.me()
        for course in client.courses.list():
            print(course.title)
    """

    def __init__(self, base_url: str, login: BaseLogin):
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": _UA})
        self.session_id: Optional[str] = None
        self.user_id: Optional[int] = None

        # Authenticate
        self.session_id = login.authenticate(self._session, self.base_url)
        if self.session_id:
            self._session.headers["X-SESSION-ID"] = self.session_id

        # Resolve user ID
        profile_data = self._session.get(f"{self.base_url}/api/profile").json()
        self.user_id = profile_data.get("id")

        # Bind API namespaces
        self.profile       = ProfileAPI(self)
        self.courses       = CoursesAPI(self)
        self.rollcall      = RollcallAPI(self)
        self.assignments   = AssignmentsAPI(self)
        self.forum         = ForumAPI(self)
        self.notifications = NotificationsAPI(self)
        self.activities    = ActivitiesAPI(self)

    # ── Low-level HTTP helpers ──────────────────────────────

    def _get(self, path: str, **kwargs) -> dict:
        return self._request("GET", path, **kwargs)

    def _post(self, path: str, **kwargs) -> dict:
        return self._request("POST", path, **kwargs)

    def _put(self, path: str, **kwargs) -> dict:
        return self._request("PUT", path, **kwargs)

    def _delete(self, path: str, **kwargs) -> dict:
        return self._request("DELETE", path, **kwargs)

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.base_url}{path}"
        resp = self._session.request(method, url, **kwargs)
        if resp.status_code == 401:
            from .exceptions import AuthError
            raise AuthError("Session expired or not authenticated.", 401, resp)
        if resp.status_code == 403:
            from .exceptions import PermissionError
            raise PermissionError("Access denied.", 403, resp)
        if resp.status_code == 404:
            from .exceptions import NotFoundError
            raise NotFoundError(f"Resource not found: {path}", 404, resp)
        if not resp.ok:
            raise TronClassError(
                f"Request failed [{resp.status_code}]: {path}", resp.status_code, resp
            )
        try:
            return resp.json()
        except Exception:
            return {}

    def push_listener(self):
        """Return a :class:`~tronclass.api.push.PushListener` bound to this client.

        The listener handles FCM/OneSignal, Socket.IO, and ntf-WebSocket channels.

        Example::

            listener = client.push_listener()
            listener.on_rollcall(lambda rc: client.rollcall.auto_answer(rc))
            import asyncio
            asyncio.run(listener.listen())
        """
        from .api.push import PushListener
        return PushListener(self)
