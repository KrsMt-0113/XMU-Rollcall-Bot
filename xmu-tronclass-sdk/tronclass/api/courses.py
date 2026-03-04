"""Courses API."""

from typing import List, Optional
from . import APINamespace
from ..models import Course, Activity


class CoursesAPI(APINamespace):
    """Course listing and management.

    Access via ``client.courses``.
    """

    _COURSE_FIELDS = (
        "id,name,course_code,department(id,name),grade(id,name),klass(id,name),"
        "course_type,cover,small_cover,start_date,end_date,is_started,is_closed,"
        "academic_year_id,semester_id,credit,compulsory,second_name,display_name,"
        "created_user(id,name),org(is_enterprise_or_organization),org_id,"
        "public_scope,audit_status,is_instructor,is_team_teaching,"
        "is_default_course_cover,archived,"
        "instructors(id,name,email,avatar_small_url),"
        "course_attributes(teaching_class_name,is_during_publish_period,"
        "copy_status,tip,data,audience_type,graduate_method),"
        "user_stick_course_record(id)"
    )

    def list(
        self,
        page: int = 1,
        page_size: int = 50,
        semester_id: Optional[int] = None,
        academic_year_id: Optional[int] = None,
    ) -> List[Course]:
        """List courses the current user is enrolled in.

        Args:
            page: Page number (1-indexed).
            page_size: Results per page.
            semester_id: Filter by semester ID.
            academic_year_id: Filter by academic year ID (required with semester_id).

        Returns:
            List of :class:`~tronclass.models.Course`.
        """
        conditions: dict = {
            "keyword": "",
            "classify_type": "recently_started",
            "display_studio_list": False,
        }
        if semester_id:
            conditions["semester_id"] = [str(semester_id)]
        if academic_year_id:
            conditions["academic_year_id"] = [str(academic_year_id)]

        body = {
            "fields": self._COURSE_FIELDS,
            "page": page,
            "page_size": page_size,
            "conditions": conditions,
            "showScorePassedStatus": False,
        }
        data = self._post("/api/my-courses", json=body)
        courses = data if isinstance(data, list) else data.get("courses", data.get("results", []))
        return [self._parse_course(c) for c in courses]

    def get_semesters(self) -> List[dict]:
        """Return a list of semesters available to the current user."""
        data = self._get("/api/my-semesters", params={"fields": "id,name,sort,academic_year_id,is_active,code"})
        return data if isinstance(data, list) else data.get("semesters", data.get("results", []))

    def get(self, course_id: int) -> Course:
        """Get details for a single course."""
        d = self._get(f"/api/course/{course_id}")
        return self._parse_course(d)

    def get_activities(
        self,
        course_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> List[Activity]:
        """List activities (assignments, exams, videos, etc.) in a course."""
        params = {"page": page, "page_size": page_size}
        data = self._get(f"/api/courses/{course_id}/activities", params=params)
        items = data if isinstance(data, list) else data.get("activities", data.get("results", []))
        return [self._parse_activity(a, course_id) for a in items]

    def get_bulletins(self, course_id: int) -> List[dict]:
        """Return course announcements/bulletins."""
        data = self._get(f"/api/courses/{course_id}/bulletins")
        return data if isinstance(data, list) else data.get("bulletins", data.get("results", []))

    def get_coursewares(self, course_id: int) -> List[dict]:
        """Return course courseware items."""
        data = self._get(f"/api/course/{course_id}/coursewares")
        return data if isinstance(data, list) else data.get("coursewares", data.get("results", []))

    def get_activity_attachments(self, activity_id: int) -> List[dict]:
        """Return attachment list for a material-type activity.

        Uses ``/api/activities/{id}/upload_references``.
        Each item has ``id`` and ``name`` fields.
        """
        data = self._get(f"/api/activities/{activity_id}/upload_references")
        refs = (
            data.get("referances")  # note: API typo
            or data.get("references")
            or data.get("value")
            or (data if isinstance(data, list) else [])
        )
        return [
            {
                "id": r.get("id") or r.get("reference_id"),
                "name": r.get("name") or r.get("reference_name") or r.get("title") or "untitled",
            }
            for r in refs
        ]

    def get_attachment_url(self, file_id: int) -> str:
        """Return a signed download URL for an upload reference file.

        Uses ``/api/uploads/reference/document/{id}/url?preview=true``.
        Returns the ``url`` string on success or raises on failure.
        """
        data = self._get(
            f"/api/uploads/reference/document/{file_id}/url",
            params={"preview": "true"},
        )
        url = data.get("url") if isinstance(data, dict) else None
        if not url:
            raise ValueError(f"No download URL returned for file {file_id}: {data}")
        return url

    def get_syllabus(self, course_id: int) -> dict:
        """Return the course syllabus."""
        return self._get(f"/api/syllabus/{course_id}")

    def get_modules(self, course_id: int) -> List[dict]:
        """Return course modules (learning units)."""
        return self._get(f"/api/modules/{course_id}")

    def get_groups(self, course_id: int) -> List[dict]:
        """Return student groups in a course."""
        return self._get(f"/api/groups/{course_id}")

    def get_enrollments(self, course_id: int) -> List[dict]:
        """Return enrollment list for a course."""
        return self._get(f"/api/enrollment/{course_id}")

    def get_rollcall_status(self, course_id: int) -> dict:
        """Return rollcall (attendance) status summary for a course."""
        return self._get(f"/api/courses/rollcall_status/{course_id}")

    def get_inclass_report(self, course_id: int) -> dict:
        """Return in-class activity report for a course."""
        return self._get(f"/api/inclass-report/{course_id}")

    def get_interactions(self, course_id: int) -> List[dict]:
        """Return in-class interaction records for a course (danmu, votes, etc.)."""
        return self._get(f"/api/courses/interactions/{course_id}")

    def get_interaction(self, course_id: int, interaction_id: int) -> dict:
        """Return a specific interaction."""
        return self._get(f"/api/courses/interactions/{course_id}/{interaction_id}")

    def search_public(self, keyword: str, page: int = 1) -> dict:
        """Search public courses by keyword."""
        return self._get("/api/courses/public", params={"page": page, "keywords": keyword})

    def join_by_code(self, access_code: str) -> dict:
        """Enroll in a course using an access code."""
        return self._post("/api/course/enrollments/join/", json={"code": access_code})

    # ── internal helpers ──

    @staticmethod
    def _parse_course(d: dict) -> Course:
        instructors = d.get("instructors") or d.get("teachers") or []
        teacher = (
            d.get("teacher_name")
            or (instructors[0].get("name") if instructors else None)
        )
        return Course(
            id=d.get("id", 0),
            title=d.get("title", d.get("name", "")),
            code=d.get("code") or d.get("course_code"),
            semester=d.get("semester", {}).get("name") if isinstance(d.get("semester"), dict) else d.get("semester"),
            teacher=teacher,
            cover=d.get("cover"),
            is_active=d.get("is_active", True),
            raw=d,
        )

    @staticmethod
    def _parse_activity(d: dict, course_id: int) -> Activity:
        return Activity(
            id=d.get("id", 0),
            title=d.get("title", d.get("name", "")),
            type=d.get("type", d.get("activity_type", "")),
            course_id=course_id,
            is_published=d.get("is_published", True),
            raw=d,
        )
