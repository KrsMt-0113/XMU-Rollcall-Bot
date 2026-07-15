import unittest
from unittest.mock import patch

from xmu_rollcall.rollcall_handler import (
    extract_rollcalls,
    handle_rollcalls,
    process_rollcalls,
)


SELF_REGISTRATION = {
    "rollcalls": [
        {
            "id": 123,
            "course_title": "Test course",
            "created_by_name": "Teacher",
            "department_name": "Department",
            "is_expired": False,
            "is_number": False,
            "is_radar": False,
            "rollcall_status": "in_progress",
            "scored": True,
            "source": "manual",
            "type": "self_registration",
            "status": "absent",
        }
    ]
}


class RollcallHandlerTests(unittest.TestCase):
    def test_extracts_self_registration_and_id_fallback(self):
        count, rollcalls = extract_rollcalls(SELF_REGISTRATION)

        self.assertEqual(count, 1)
        self.assertEqual(rollcalls[0]["rollcall_id"], 123)
        self.assertEqual(rollcalls[0]["type"], "self_registration")

    @patch("xmu_rollcall.rollcall_handler.attendance_threshold_reached")
    def test_already_answered_bypasses_threshold(self, threshold):
        data = {"rollcalls": [dict(SELF_REGISTRATION["rollcalls"][0], status="on_call")]}

        result = handle_rollcalls(data, object(), 0.2)

        self.assertEqual(result, [True])
        threshold.assert_not_called()

    @patch("xmu_rollcall.rollcall_handler.send_self_registration", return_value=True)
    @patch(
        "xmu_rollcall.rollcall_handler.attendance_threshold_reached",
        return_value=(True, {"student_rollcalls": []}),
    )
    def test_answers_self_registration_after_threshold(self, threshold, send):
        session = object()
        result = handle_rollcalls(SELF_REGISTRATION, session, 0.2)

        self.assertEqual(result, [True])
        threshold.assert_called_once_with(session, 123, 0.2)
        send.assert_called_once_with(session, 123)

    @patch(
        "xmu_rollcall.rollcall_handler.attendance_threshold_reached",
        return_value=(False, {"student_rollcalls": []}),
    )
    def test_pending_rollcall_is_retried(self, threshold):
        result = process_rollcalls(SELF_REGISTRATION, object(), 0.2)

        self.assertEqual(result, {"rollcalls": []})


if __name__ == "__main__":
    unittest.main()
