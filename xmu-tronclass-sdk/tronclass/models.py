"""Data models (dataclasses) for TronClass API responses."""

from dataclasses import dataclass, field
from typing import Optional, List, Any


@dataclass
class User:
    id: int
    name: str
    email: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[str] = None
    raw: dict = field(default_factory=dict, repr=False)


@dataclass
class Course:
    id: int
    title: str
    code: Optional[str] = None
    semester: Optional[str] = None
    teacher: Optional[str] = None
    cover: Optional[str] = None
    is_active: bool = True
    raw: dict = field(default_factory=dict, repr=False)


@dataclass
class Activity:
    id: int
    title: str
    type: str  # e.g. "homework", "exam", "rollcall", "video"
    course_id: Optional[int] = None
    is_published: bool = True
    raw: dict = field(default_factory=dict, repr=False)


@dataclass
class Rollcall:
    rollcall_id: int
    course_title: str
    created_by_name: str
    department_name: str
    is_number: bool
    is_radar: bool
    is_qrcode: bool
    is_expired: bool
    status: str          # 'absent' | 'on_call_fine' | ...
    rollcall_status: str
    scored: bool
    raw: dict = field(default_factory=dict, repr=False)

    @property
    def rollcall_type(self) -> str:
        if self.is_radar:
            return "RADAR"
        if self.is_number:
            return "NUMBER"
        return "QRCODE"

    @property
    def is_answered(self) -> bool:
        return self.status == "on_call_fine"

    @classmethod
    def from_dict(cls, d: dict) -> "Rollcall":
        return cls(
            rollcall_id=d["rollcall_id"],
            course_title=d.get("course_title", ""),
            created_by_name=d.get("created_by_name", ""),
            department_name=d.get("department_name", ""),
            is_number=d.get("is_number", False),
            is_radar=d.get("is_radar", False),
            is_qrcode=not d.get("is_number", False) and not d.get("is_radar", False),
            is_expired=d.get("is_expired", False),
            status=d.get("status", ""),
            rollcall_status=d.get("rollcall_status", ""),
            scored=d.get("scored", False),
            raw=d,
        )


@dataclass
class Homework:
    id: int
    title: str
    course_id: int
    due_at: Optional[str] = None
    submitted: bool = False
    score: Optional[float] = None
    raw: dict = field(default_factory=dict, repr=False)


@dataclass
class Topic:
    id: int
    title: str
    content: Optional[str] = None
    course_id: Optional[int] = None
    author: Optional[str] = None
    replies_count: int = 0
    raw: dict = field(default_factory=dict, repr=False)


@dataclass
class Notification:
    id: int
    message: str
    is_read: bool = False
    created_at: Optional[str] = None
    raw: dict = field(default_factory=dict, repr=False)
