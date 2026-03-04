"""XMU (Xiamen University) OAuth2 login.

Implements the full XMU Unified Identity Authentication flow:
  1. Start OAuth2 authorization on ids.xmu.edu.cn
  2. Follow redirects to the login form
  3. Extract AES salt + execution token from form
  4. Submit AES-CBC encrypted password
  5. Exchange authorization code for access token
  6. POST access_token to TronClass /api/login
"""

import base64
import random
import re
import requests
from urllib.parse import urlparse, parse_qs

from .base import BaseLogin
from ..exceptions import AuthError

_AES_CHARS = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
_UA = (
    "Mozilla/5.0 (Linux; Android 6.0; Nexus 5) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/142.0.0.0 Mobile Safari/537.36"
)
_IDENTITY_BASE = "https://c-identity.xmu.edu.cn"
_CALLBACK = "https://c-mobile.xmu.edu.cn/identity-web-login-callback?_h5=true"
_CLIENT_ID = "TronClassH5"


def _rand(n: int) -> str:
    return "".join(random.choice(_AES_CHARS) for _ in range(n))


def _encrypt_password(password: str, salt: str) -> str:
    """AES-128-CBC encrypt password with random 64-char padding, as required by XMU portal."""
    from Crypto.Cipher import AES

    plaintext = _rand(64) + password
    iv = _rand(16).encode()
    cipher = AES.new(salt.encode(), AES.MODE_CBC, iv)
    pad = 16 - len(plaintext) % 16
    encrypted = cipher.encrypt((plaintext + chr(pad) * pad).encode())
    return base64.b64encode(encrypted).decode()


class XMULogin(BaseLogin):
    """Login to TronClass via Xiamen University Unified Identity Authentication.

    Supports any TronClass instance that uses the XMU identity server
    (``c-identity.xmu.edu.cn``).

    Args:
        username: XMU student/staff ID.
        password: XMU portal password (plaintext; encrypted before sending).

    Example::

        from tronclass import TronClassClient
        from tronclass.auth import XMULogin

        client = TronClassClient(
            "https://lnt.xmu.edu.cn",
            XMULogin("your_student_id", "your_password"),
        )
    """

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def authenticate(self, session: requests.Session, base_url: str) -> str:
        h = {"User-Agent": _UA}
        params = {
            "scope": "openid",
            "response_type": "code",
            "client_id": _CLIENT_ID,
            "redirect_uri": _CALLBACK,
        }

        try:
            # Step 1 — Start OAuth2 flow
            r1 = session.get(
                f"{_IDENTITY_BASE}/auth/realms/xmu/protocol/openid-connect/auth",
                headers=h, params=params, allow_redirects=False,
            )
            loc = r1.headers["location"]

            # Step 2 — Follow to login form
            loc = session.get(loc, headers=h, allow_redirects=False).headers["location"]
            r3 = session.get(loc, headers=h)

            # Step 3 — Extract AES salt + execution token
            salt = re.search(r'id="pwdEncryptSalt"\s+value="([^"]+)"', r3.text)
            execution = re.search(r'name="execution"\s+value="([^"]+)"', r3.text)
            if not salt or not execution:
                raise AuthError("Could not find login form fields — XMU login page may have changed.")

            # Step 4 — Submit credentials
            data = {
                "username": self.username,
                "password": _encrypt_password(self.password, salt.group(1)),
                "captcha": "",
                "_eventId": "submit",
                "cllt": "userNameLogin",
                "dllt": "generalLogin",
                "lt": "",
                "execution": execution.group(1),
            }
            r4 = session.post(r3.url, data=data, headers=h, allow_redirects=False)
            if "location" not in r4.headers:
                raise AuthError("Login failed — wrong username or password.")
            loc = r4.headers["location"]

            # Step 5 — Follow redirect chain to extract authorization code
            r5 = session.get(loc, headers=h, allow_redirects=False)
            if "location" not in r5.headers:
                raise AuthError("Unexpected redirect after login.")
            code_url = r5.headers["location"]
            code = parse_qs(urlparse(code_url).query).get("code", [None])[0]
            if not code:
                raise AuthError("Authorization code not found in redirect URL.")

            # Step 6 — Exchange code for access token
            token_resp = session.post(
                f"{_IDENTITY_BASE}/auth/realms/xmu/protocol/openid-connect/token",
                data={
                    "client_id": _CLIENT_ID,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": _CALLBACK,
                    "scope": "openid",
                },
            )
            token_resp.raise_for_status()
            access_token = token_resp.json().get("access_token")
            if not access_token:
                raise AuthError("Failed to obtain access token from identity server.")

            # Step 7 — Login to TronClass
            session.post(
                f"{base_url}/api/login?login=access_token",
                json={"access_token": access_token, "org_id": 1},
            )

            # Step 8 — Get session ID from profile
            profile = session.get(f"{base_url}/api/profile")
            profile.raise_for_status()
            return profile.headers.get("X-SESSION-ID", "")

        except AuthError:
            raise
        except Exception as e:
            raise AuthError(f"XMU login failed: {e}") from e
