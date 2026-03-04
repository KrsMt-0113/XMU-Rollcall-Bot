"""Activities (generic content items) API."""

from typing import List, Optional
from . import APINamespace
from ..models import Activity


class ActivitiesAPI(APINamespace):
    """Generic activity access — video, live, courseware quiz, interaction, etc.

    Access via ``client.activities``.
    """

    def get(self, activity_id: int) -> Activity:
        """Get a single activity by ID."""
        d = self._get(f"/api/activities/{activity_id}")
        return Activity(
            id=d.get("id", activity_id),
            title=d.get("title", d.get("name", "")),
            type=d.get("type", d.get("activity_type", "")),
            course_id=d.get("course_id"),
            is_published=d.get("is_published", True),
            raw=d,
        )

    def list_user_activities(
        self,
        page: int = 1,
        page_size: int = 30,
        activity_type: Optional[str] = None,
    ) -> List[dict]:
        """Return activities visible to the current user across all courses.

        Args:
            page: Page number.
            page_size: Results per page.
            activity_type: Filter by type (e.g. ``"homework"``, ``"video"``).
        """
        params: dict = {"page": page, "page_size": page_size}
        if activity_type:
            params["type"] = activity_type
        return self._get("/api/user/courses/activities", params=params)

    def mark_read(self, activity_id: int, course_id: int) -> dict:
        """Mark an activity as read/viewed.

        Args:
            activity_id: Activity ID.
            course_id: The course the activity belongs to.
        """
        return self._post(
            f"/api/course/activity-read/{course_id}",
            json={"activity_id": activity_id},
        )

    def get_courseware_quiz(self, activity_id: int) -> dict:
        """Return courseware quiz details for an activity."""
        return self._get(f"/api/courseware-quiz/activity/{activity_id}")

    def get_online_video(self, activity_id: int) -> dict:
        """Return online video details for an activity."""
        return self._get(f"/api/online-videos/{activity_id}")

    def list_interaction_activities(self, course_id: int) -> List[dict]:
        """Return in-class interaction activities for a course."""
        return self._get(f"/api/interaction-activities/{course_id}")

    def list_live_activities(self) -> List[dict]:
        """Return upcoming/active live lecture activities."""
        return self._get("/api/courses/lecture-live-activity/")

    def get_public_lives(self) -> List[dict]:
        """Return publicly accessible live stream activities."""
        return self._get("/api/public-lives")

    def get_shared_resources(
        self,
        page: int = 1,
        page_size: int = 30,
        keyword: Optional[str] = None,
    ) -> dict:
        """Browse the shared resource library.

        Args:
            page: Page number.
            page_size: Results per page.
            keyword: Optional search keyword.
        """
        params: dict = {"page": page, "page_size": page_size}
        if keyword:
            params["keywords"] = keyword
        return self._get("/api/shared-resources/", params=params)

    def get_notebooks(self, course_id: Optional[int] = None) -> List[dict]:
        """Return study notebooks, optionally filtered by course."""
        params = {}
        if course_id:
            params["course_id"] = course_id
        return self._get("/api/notebooks/", params=params)
