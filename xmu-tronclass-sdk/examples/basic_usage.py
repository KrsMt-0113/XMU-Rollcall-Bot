"""Basic usage example for XMU-Tronclass-SDK."""

from tronclass import TronClassClient
from tronclass.auth import XMULogin, TokenLogin

# ── Option 1: XMU login (recommended for XMU students) ────────────
client = TronClassClient(
    "https://lnt.xmu.edu.cn",
    XMULogin("your_xmu_username", "your_xmu_password"),
)

# ── Option 2: Token login (any TronClass instance) ─────────────────
# client = TronClassClient(
#     "https://lnt.xmu.edu.cn",
#     TokenLogin("your_jwt_token"),
# )

# ── Profile ────────────────────────────────────────────────────────
me = client.profile.me()
print(f"Logged in as: {me.name} ({me.user_type})")

# ── Courses ────────────────────────────────────────────────────────
courses = client.courses.list()
print(f"\nCourses ({len(courses)}):")
for course in courses:
    print(f"  [{course.course_id}] {course.title} — {course.teacher_name}")

# ── Activities (recent) ────────────────────────────────────────────
if courses:
    first_course = courses[0]
    activities = client.activities.list_by_course(first_course.course_id)
    print(f"\nActivities in '{first_course.title}':")
    for act in activities[:5]:
        print(f"  {act.activity_type}: {act.title}")

# ── Active rollcalls ───────────────────────────────────────────────
active = client.rollcall.list_active()
print(f"\nActive rollcalls: {len(active)}")
for rc in active:
    print(f"  [{rc.rollcall_id}] {rc.rollcall_type} — {rc.course_title}")
    result = client.rollcall.auto_answer(rc)
    print(f"  → {result}")

# ── Assignments ────────────────────────────────────────────────────
homeworks = client.assignments.list()
print(f"\nPending assignments: {len(homeworks)}")
for hw in homeworks[:5]:
    print(f"  {hw.title} (due: {hw.end_time})")

# ── Notifications ──────────────────────────────────────────────────
notifications = client.notifications.list(unread_only=True)
print(f"\nUnread notifications: {len(notifications)}")
for n in notifications[:3]:
    print(f"  [{n.type}] {n.message}")
