"""Forum and discussion API."""

from typing import List, Optional
from . import APINamespace
from ..models import Topic


class ForumAPI(APINamespace):
    """Course forum, topics, and replies.

    Access via ``client.forum``.
    """

    def list_topics(
        self,
        course_id: int,
        page: int = 1,
        page_size: int = 30,
    ) -> List[Topic]:
        """List discussion topics in a course.

        Args:
            course_id: Course ID.
            page: Page number.
            page_size: Results per page.
        """
        params = {"course_id": course_id, "page": page, "page_size": page_size}
        data = self._get("/api/topics", params=params)
        items = data if isinstance(data, list) else data.get("topics", data.get("results", []))
        return [self._parse_topic(t) for t in items]

    def get_topic(self, topic_id: int) -> Topic:
        """Get a single topic by ID."""
        d = self._get(f"/api/topics/{topic_id}")
        return self._parse_topic(d)

    def get_topped_topics(self, course_id: int) -> List[Topic]:
        """Return pinned/topped topics in a course."""
        data = self._get("/api/topics/topped", params={"course_id": course_id})
        items = data if isinstance(data, list) else data.get("topics", [])
        return [self._parse_topic(t) for t in items]

    def create_topic(
        self,
        course_id: int,
        title: str,
        content: str,
        is_anonymous: bool = False,
    ) -> Topic:
        """Create a new discussion topic.

        Args:
            course_id: Course to post in.
            title: Topic title.
            content: Topic body text.
            is_anonymous: Post anonymously.
        """
        d = self._post(
            "/api/topics/",
            json={
                "course_id": course_id,
                "title": title,
                "content": content,
                "is_anonymous": is_anonymous,
            },
        )
        return self._parse_topic(d)

    def reply(
        self,
        topic_id: int,
        content: str,
        parent_reply_id: Optional[int] = None,
        is_anonymous: bool = False,
    ) -> dict:
        """Post a reply to a topic.

        Args:
            topic_id: Topic ID to reply to.
            content: Reply text.
            parent_reply_id: Optional parent reply ID for nested replies.
            is_anonymous: Post anonymously.
        """
        payload: dict = {
            "topic_id": topic_id,
            "content": content,
            "is_anonymous": is_anonymous,
        }
        if parent_reply_id:
            payload["parent_id"] = parent_reply_id
        return self._post("/api/replies/", json=payload)

    def delete_reply(self, reply_id: int) -> dict:
        """Delete a reply."""
        return self._delete(f"/api/replies/{reply_id}")

    def list_forum_categories(self, course_id: int) -> List[dict]:
        """List forum categories in a course."""
        return self._get(f"/api/forum/categories/{course_id}")

    def ask_question(self, course_id: int, content: str) -> dict:
        """Post a question in the course Q&A section."""
        return self._post(
            "/api/courses/ask-questions/",
            json={"course_id": course_id, "content": content},
        )

    def list_questions(self, course_id: int) -> List[dict]:
        """List Q&A questions in a course."""
        return self._get(f"/api/courses/ask-questions/{course_id}")

    # ── Internal ──

    @staticmethod
    def _parse_topic(d: dict) -> Topic:
        author = d.get("author") or d.get("created_by") or {}
        return Topic(
            id=d.get("id", 0),
            title=d.get("title", ""),
            content=d.get("content"),
            course_id=d.get("course_id"),
            author=author.get("name") if isinstance(author, dict) else str(author),
            replies_count=d.get("replies_count", 0),
            raw=d,
        )
