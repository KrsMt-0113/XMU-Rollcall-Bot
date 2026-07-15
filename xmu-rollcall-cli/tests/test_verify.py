import unittest
from unittest.mock import patch

from xmu_rollcall.verify import (
    attendance_threshold_reached,
    calculate_attendance_progress,
    send_code,
    send_self_registration,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, get_response=None, put_response=None):
        self.headers = {"User-Agent": "test"}
        self.get_response = get_response or FakeResponse()
        self.put_response = put_response or FakeResponse()
        self.get_calls = []
        self.put_calls = []

    def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        return self.get_response

    def put(self, url, **kwargs):
        self.put_calls.append((url, kwargs))
        return self.put_response


class AttendanceTests(unittest.TestCase):
    def test_calculates_signed_ratio(self):
        progress = calculate_attendance_progress(
            {
                "student_rollcalls": [
                    {"status": "on_call"},
                    {"status": "on_call_fine"},
                    {"status": "absent"},
                    {"status": "absent"},
                ]
            }
        )

        self.assertEqual(progress, (2, 4, 0.5))

    def test_waits_below_threshold_and_reuses_payload(self):
        payload = {
            "number_code": "1234",
            "student_rollcalls": [
                {"status": "on_call"},
                {"status": "absent"},
                {"status": "absent"},
                {"status": "absent"},
                {"status": "absent"},
                {"status": "absent"},
            ],
        }
        session = FakeSession(get_response=FakeResponse(payload=payload))

        reached, details = attendance_threshold_reached(session, 42, 0.2)

        self.assertFalse(reached)
        self.assertIs(details, payload)
        self.assertEqual(len(session.get_calls), 1)

    def test_zero_threshold_does_not_call_api(self):
        session = FakeSession()

        reached, details = attendance_threshold_reached(session, 42, 0)

        self.assertTrue(reached)
        self.assertIsNone(details)
        self.assertEqual(session.get_calls, [])

    @patch("xmu_rollcall.verify.time.sleep")
    def test_number_rollcall_reuses_attendance_response(self, sleep):
        session = FakeSession()
        details = {"number_code": "5678", "student_rollcalls": []}

        result = send_code(session, 42, details)

        self.assertTrue(result)
        self.assertEqual(session.get_calls, [])
        url, kwargs = session.put_calls[0]
        self.assertTrue(url.endswith("/42/answer_number_rollcall"))
        self.assertEqual(kwargs["json"]["numberCode"], "5678")
        sleep.assert_called_once_with(5)

    def test_self_registration_payload(self):
        session = FakeSession()

        result = send_self_registration(session, 99)

        self.assertTrue(result)
        url, kwargs = session.put_calls[0]
        self.assertTrue(url.endswith("/99/answer_self_registration_rollcall"))
        self.assertEqual(set(kwargs["json"]), {"deviceId"})
        self.assertTrue(kwargs["json"]["deviceId"])


if __name__ == "__main__":
    unittest.main()
