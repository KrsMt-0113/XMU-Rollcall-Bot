"""Notifications and todos API."""

from typing import List, Optional
from . import APINamespace
from ..models import Notification


class NotificationsAPI(APINamespace):
    """Alert messages and to-do items.

    Access via ``client.notifications``.
    """

    def list_alerts(
        self,
        page: int = 1,
        page_size: int = 50,
        unread_only: bool = False,
    ) -> List[Notification]:
        """List notifications via /ntf/users/{user_id}/notifications."""
        user_id = self._client.user_id
        if not user_id:
            return []
        params: dict = {"page": page, "page_size": page_size}
        if unread_only:
            params["unread"] = True
        data = self._get(f"/ntf/users/{user_id}/notifications", params=params)
        items = data if isinstance(data, list) else data.get("notifications", data.get("results", data.get("data", [])))
        return [self._parse_notification(n) for n in items]

    def mark_read(self, message_ids: Optional[List[int]] = None) -> dict:
        """Mark alert messages as read.

        Args:
            message_ids: List of message IDs to mark. If omitted, marks all as read.
        """
        payload = {"ids": message_ids} if message_ids else {}
        return self._post("/api/alert/messages/read", json=payload)

    def list_todos(self) -> List[dict]:
        """Return the user's to-do list (pending tasks across all courses)."""
        return self._get("/api/todos")

    def list_org_bulletins(self, page: int = 1) -> List[dict]:
        """Return institution-wide bulletin announcements."""
        return self._get("/api/org-bulletin/bulletins", params={"page": page})

    def get_org_bulletin(self, bulletin_id: int) -> dict:
        """Get details of an institution bulletin."""
        return self._get(f"/api/org-bulletin/bulletins/{bulletin_id}")

    def list_bulletins(self, course_id: Optional[int] = None) -> List[dict]:
        """Return course or general bulletins.

        Args:
            course_id: Filter by course. If omitted, returns global bulletins.
        """
        params = {}
        if course_id:
            params["course_id"] = course_id
        return self._get("/api/bulletins/", params=params)

    @staticmethod
    def _format_message(ntf_type: str, payload: dict) -> str:
        """Convert notification type + payload to a human-readable string."""
        course = payload.get("course_name", "")
        pfx = f"[{course}] " if course else ""

        if ntf_type == "homework_score_updated":
            title = payload.get("activity_title", "作业")
            score = payload.get("score", "?")
            return f"{pfx}作业评分：{title} — {score} 分"
        if ntf_type == "homework_submitted":
            title = payload.get("activity_title", "作业")
            return f"{pfx}作业已提交：{title}"
        if ntf_type == "homework_comment":
            title = payload.get("activity_title", "作业")
            return f"{pfx}作业评论：{title}"
        if ntf_type in ("exam_opened", "exam_published"):
            title = payload.get("exam_title") or payload.get("activity_title", "考试")
            return f"{pfx}考试开放：{title}"
        if ntf_type == "exam_score_updated":
            title = payload.get("exam_title") or payload.get("activity_title", "考试")
            score = payload.get("score", "?")
            return f"{pfx}考试评分：{title} — {score} 分"
        if ntf_type in ("rollcall_started", "rollcall"):
            return f"{pfx}签到开始"
        if ntf_type == "course_bulletin":
            title = payload.get("bulletin_title") or payload.get("title", "公告")
            return f"{pfx}课程公告：{title}"
        if ntf_type == "activity_published":
            title = payload.get("activity_title") or payload.get("title", "")
            atype = payload.get("activity_type", "活动")
            return f"{pfx}{atype} 发布：{title}"
        # fallback: show type + any title-like field
        title = (payload.get("activity_title") or payload.get("title")
                 or payload.get("exam_title") or "")
        label = ntf_type.replace("_", " ")
        return f"{pfx}{label}" + (f"：{title}" if title else "")

    @staticmethod
    def _parse_notification(d: dict) -> Notification:
        payload = d.get("payload") or {}
        ntf_type = d.get("type", "")
        ts = d.get("timestamp")
        created = (
            payload.get("created_at")
            or (str(int(ts) // 1000) if ts else None)
        )
        return Notification(
            id=d.get("id", 0),
            message=NotificationsAPI._format_message(ntf_type, payload),
            is_read=not d.get("unread", True),
            created_at=created,
            raw=d,
        )
