"""Authentication fallbacks based on imported or browser-captured cookies."""

from __future__ import annotations

import json
import sys
import time
from http.cookies import CookieError, SimpleCookie
from typing import Any, Dict, Iterable, Optional

import requests

BASE_URL = "https://lnt.xmu.edu.cn"
PROFILE_URL = f"{BASE_URL}/api/profile"


class CookieImportError(ValueError):
    """Raised when cookie input cannot be parsed into a usable session."""


def _set_cookie(session: requests.Session, item: Dict[str, Any]) -> None:
    name = item.get("name")
    value = item.get("value")
    if not name or value is None:
        raise CookieImportError("Cookie entries must include name and value fields.")

    kwargs: Dict[str, Any] = {}
    for key in ("domain", "path"):
        if item.get(key):
            kwargs[key] = item[key]
    if item.get("secure") is not None:
        kwargs["secure"] = bool(item["secure"])

    expires = item.get("expires", item.get("expirationDate"))
    if expires not in (None, "", -1):
        try:
            kwargs["expires"] = int(float(expires))
        except (TypeError, ValueError):
            pass

    session.cookies.set(str(name), str(value), **kwargs)


def _load_json_cookies(session: requests.Session, payload: Any) -> bool:
    if isinstance(payload, dict) and isinstance(payload.get("cookies"), list):
        payload = payload["cookies"]

    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                raise CookieImportError("A JSON cookie list may only contain objects.")
            _set_cookie(session, item)
        return bool(payload)

    if isinstance(payload, dict):
        for name, value in payload.items():
            if isinstance(value, (dict, list)):
                raise CookieImportError(
                    "A JSON cookie object must map cookie names directly to values."
                )
            session.cookies.set(str(name), str(value))
        return bool(payload)

    return False


def session_from_cookie_input(cookie_input: str) -> requests.Session:
    """Build a requests session from JSON exports or a raw Cookie header.

    Supported JSON shapes are the bot's ``{name: value}`` cache, a browser
    extension's list of cookie objects, and ``{"cookies": [...]}`` exports.
    """

    value = (cookie_input or "").strip()
    if not value:
        raise CookieImportError("Cookie input is empty.")

    session = requests.Session()
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        payload = None

    if payload is not None:
        if not _load_json_cookies(session, payload):
            raise CookieImportError("The JSON input does not contain any cookies.")
        return session

    if value.lower().startswith("cookie:"):
        value = value.split(":", 1)[1].strip()

    parsed = SimpleCookie()
    try:
        parsed.load(value)
    except CookieError as exc:  # pragma: no cover - depends on stdlib parser
        raise CookieImportError(f"Invalid Cookie header: {exc}") from exc

    if not parsed:
        raise CookieImportError(
            "Unsupported cookie format. Use JSON or a raw 'name=value; ...' header."
        )
    for name, morsel in parsed.items():
        session.cookies.set(name, morsel.value)
    return session


def capture_browser_session(timeout: int = 300) -> requests.Session:
    """Open an interactive Chromium login and return its authenticated cookies."""

    if sys.version_info < (3, 8):
        raise RuntimeError("Browser login requires Python 3.8 or newer.")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Browser login requires the optional dependency. Run "
            "`pip install 'xmu-rollcall-cli[browser]'` and "
            "`playwright install chromium`."
        ) from exc

    deadline = time.monotonic() + timeout
    captured: Optional[Iterable[Dict[str, Any]]] = None

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(BASE_URL, wait_until="domcontentloaded")

        while time.monotonic() < deadline:
            try:
                response = context.request.get(PROFILE_URL, timeout=5000)
                if response.status == 200:
                    profile = response.json()
                    if isinstance(profile, dict) and profile.get("name"):
                        captured = context.cookies([BASE_URL])
                        break
            except Exception:
                pass
            page.wait_for_timeout(1000)

        browser.close()

    if not captured:
        raise RuntimeError("Browser login timed out before TronClass authentication completed.")

    session = requests.Session()
    for item in captured:
        _set_cookie(session, item)
    return session
