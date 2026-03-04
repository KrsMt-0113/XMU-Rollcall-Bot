"""Assignments and submissions API."""

from typing import List, Optional
from . import APINamespace
from ..models import Homework


class AssignmentsAPI(APINamespace):
    """Homework, exams, and submission management.

    Access via ``client.assignments``.
    """

    # ── Homework ──

    def list_homework(
        self,
        course_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 30,
    ) -> List[Homework]:
        """List homework assignments.

        Args:
            course_id: Filter by course. If omitted, returns all.
            page: Page number.
            page_size: Results per page.
        """
        params: dict = {"page": page, "page_size": page_size}
        if course_id:
            params["course_id"] = course_id
        data = self._get("/api/homeworks", params=params)
        items = data if isinstance(data, list) else data.get("homeworks", data.get("results", []))
        return [self._parse_homework(h) for h in items]

    def get_homework(self, homework_id: int) -> Homework:
        """Get details of a specific homework assignment."""
        d = self._get(f"/api/homework/{homework_id}")
        return self._parse_homework(d)

    def list_submissions(
        self,
        homework_id: Optional[int] = None,
        course_id: Optional[int] = None,
    ) -> List[dict]:
        """List submissions for a homework or course."""
        params = {}
        if homework_id:
            params["homework_id"] = homework_id
        if course_id:
            params["course_id"] = course_id
        return self._get("/api/submissions/", params=params)

    def get_submission(self, submission_id: int) -> dict:
        """Get a specific submission by ID."""
        return self._get(f"/api/submission/{submission_id}")

    def submit_homework(self, homework_id: int, content: str, file_ids: List[int] = None) -> dict:
        """Submit a homework assignment.

        Args:
            homework_id: Homework assignment ID.
            content: Text content of the submission.
            file_ids: Optional list of pre-uploaded file IDs to attach.
        """
        payload: dict = {"content": content}
        if file_ids:
            payload["file_ids"] = file_ids
        return self._post(f"/api/submissions/", json={**payload, "homework_id": homework_id})

    # ── Exams ──

    def list_exams(self, course_id: Optional[int] = None) -> List[dict]:
        """List exams, optionally filtered by course."""
        params = {}
        if course_id:
            params["course_id"] = course_id
        return self._get("/api/exams/", params=params)

    def get_exam(self, exam_id: int) -> dict:
        """Get exam details."""
        return self._get(f"/api/exam/{exam_id}")

    def list_exam_submissions(self, exam_id: int) -> List[dict]:
        """List submissions for an exam."""
        return self._get(f"/api/exams/submissions/{exam_id}")

    # ── Questionnaires ──

    def list_questionnaires(self, course_id: Optional[int] = None) -> List[dict]:
        """List questionnaires/surveys."""
        params = {}
        if course_id:
            params["course_id"] = course_id
        return self._get("/api/questionnaires/", params=params)

    def get_questionnaire(self, questionnaire_id: int) -> dict:
        """Get questionnaire details."""
        return self._get(f"/api/questionnaire/{questionnaire_id}")

    # ── Feedback ──

    def list_feedbacks(self, course_id: Optional[int] = None) -> List[dict]:
        """List feedback activities."""
        params = {}
        if course_id:
            params["course_id"] = course_id
        return self._get("/api/feedbacks/", params=params)

    # ── Uploads ──

    def upload_file(self, file_path: str, file_type: str = "document") -> dict:
        """Upload a file to TronClass storage.

        Args:
            file_path: Local path to the file.
            file_type: One of ``"document"``, ``"video"``, ``"audio"``, ``"image"``.

        Returns:
            Upload response including file ID and URL.
        """
        endpoints = {
            "document": "/api/uploads/document/",
            "video": "/api/uploads/video/",
            "audio": "/api/uploads/audio/",
        }
        endpoint = endpoints.get(file_type, "/api/uploads/")
        with open(file_path, "rb") as f:
            return self._post(endpoint, files={"file": f})

    # ── Internal ──

    @staticmethod
    def _parse_homework(d: dict) -> Homework:
        return Homework(
            id=d.get("id", 0),
            title=d.get("title", d.get("name", "")),
            course_id=d.get("course_id", 0),
            due_at=d.get("due_at") or d.get("deadline"),
            submitted=d.get("submitted", False),
            score=d.get("score"),
            raw=d,
        )
