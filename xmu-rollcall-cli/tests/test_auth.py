import json
import unittest

from xmu_rollcall.auth import CookieImportError, session_from_cookie_input


class CookieImportTests(unittest.TestCase):
    def test_raw_cookie_header(self):
        session = session_from_cookie_input("Cookie: session=abc; role_token=student")

        self.assertEqual(session.cookies.get("session"), "abc")
        self.assertEqual(session.cookies.get("role_token"), "student")

    def test_browser_json_export(self):
        cookie_input = json.dumps(
            {
                "cookies": [
                    {
                        "name": "session",
                        "value": "abc",
                        "domain": "lnt.xmu.edu.cn",
                        "path": "/",
                        "secure": True,
                    }
                ]
            }
        )

        session = session_from_cookie_input(cookie_input)

        self.assertEqual(
            session.cookies.get("session", domain="lnt.xmu.edu.cn", path="/"),
            "abc",
        )

    def test_rejects_empty_json(self):
        with self.assertRaises(CookieImportError):
            session_from_cookie_input("{}")


if __name__ == "__main__":
    unittest.main()
