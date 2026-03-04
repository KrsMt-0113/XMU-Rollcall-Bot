# XMU-Tronclass-SDK

A Python SDK for the [TronClass](https://lnt.xmu.edu.cn) LMS, reverse-engineered from the official Android APK.
Supports all major features including **push-based automatic rollcall** — no polling required.

---

## Installation

```bash
cd xmu-tronclass-sdk
pip install -e .
```

Dependencies: `requests`, `pycryptodome`, `aiohttp`, `websockets`, `python-socketio`

---

## Quick Start

```python
from tronclass import TronClassClient
from tronclass.auth import XMULogin

client = TronClassClient(
    "https://lnt.xmu.edu.cn",
    XMULogin("your_username", "your_password"),
)

me = client.profile.me()
print(f"Hello, {me.name}!")

for course in client.courses.list():
    print(course.title)
```

For non-XMU instances, use `TokenLogin`:

```python
from tronclass.auth import TokenLogin
client = TronClassClient("https://your-school.tronclass.com", TokenLogin("your_jwt"))
```

---

## Features

| Module | Description |
|---|---|
| `client.profile` | User profile, avatar, notification settings |
| `client.courses` | Course list, course info, activities by course |
| `client.rollcall` | Answer rollcalls (number brute-force, radar, QR, self-registration) |
| `client.assignments` | List homework, get details |
| `client.forum` | Topics, threads, posts |
| `client.notifications` | Alert messages, todos, mark as read |
| `client.activities` | Activity details, learning progress |
| `client.push_listener()` | Real-time push notification listener (FCM + Socket.IO + ntf-WS) |

---

## API Reference

### Authentication

#### `XMULogin(username, password)`

Handles XMU's unified identity portal (AES-encrypted OAuth2 flow).

```python
from tronclass.auth import XMULogin
login = XMULogin("student_id", "password")
```

#### `TokenLogin(token)`

For any TronClass instance where you already have a JWT token.

```python
from tronclass.auth import TokenLogin
login = TokenLogin("eyJhbGciOiJIUzI1...")
```

---

### Profile — `client.profile`

```python
me = client.profile.me()
# User(user_id, name, email, phone, user_type, avatar_url, locale, ...)

client.profile.update_locale("zh-Hans")
client.profile.update_avatar("/path/to/avatar.jpg")

settings = client.profile.ntf_settings()
client.profile.update_ntf_settings({"rollcall": True, "homework": True})
```

---

### Courses — `client.courses`

```python
courses = client.courses.list()
# [Course(course_id, title, teacher_name, term, ...)]

course = client.courses.get(course_id=12345)
members = client.courses.members(course_id=12345)
```

---

### Rollcall — `client.rollcall`

The most important module. Handles 4 rollcall types:

| Type | Strategy |
|---|---|
| `NUMBER_ROLLCALL` | Brute-force `0000`–`9999` with 200 concurrent async requests |
| `RADAR_ROLLCALL` | Two-circle triangulation to find the classroom location |
| `QRCODE_ROLLCALL` | Submit the QR payload string directly |
| `SELF_REGISTRATION_ROLLCALL` | Answer with current GPS location |

```python
# List all active rollcalls
active = client.rollcall.list_active()

# Auto-detect type and answer
result = client.rollcall.auto_answer(rollcall)

# Manual control
client.rollcall.answer_number(rollcall_id, "0042")
client.rollcall.answer_qrcode(rollcall_id, qr_payload_string)
client.rollcall.answer_radar(rollcall_id, longitude=118.0, latitude=24.0)
client.rollcall.answer_self_registration(rollcall_id, longitude=118.0, latitude=24.0)

# Answer all active rollcalls at once
client.rollcall.answer_all_active()
```

---

### Assignments — `client.assignments`

```python
homeworks = client.assignments.list()
# [Homework(homework_id, title, course_title, end_time, submitted, ...)]

hw = client.assignments.get(homework_id=456)
client.assignments.submit(homework_id=456, content="My answer", attachments=[])
```

---

### Forum — `client.forum`

```python
topics = client.forum.list(course_id=12345)
# [Topic(topic_id, title, content, author, reply_count, ...)]

topic = client.forum.get(topic_id=789)
client.forum.reply(topic_id=789, content="My reply")
```

---

### Notifications — `client.notifications`

```python
msgs = client.notifications.list(unread_only=True)
# [Notification(id, type, message, created_at, is_read)]

client.notifications.mark_read(notification_id=1001)
client.notifications.mark_all_read()

todos = client.notifications.list_todos()
```

---

### Activities — `client.activities`

```python
act = client.activities.get(activity_id=5678)
acts = client.activities.list_by_course(course_id=12345)
```

---

### Push Listener — `client.push_listener()`

Listens for real-time events on **three concurrent channels**:

| Channel | Protocol | Events |
|---|---|---|
| FCM / MCS | SSL TCP → `mtalk.google.com:5228` | `NUMBER_ROLLCALL`, `RADAR_ROLLCALL`, `QRCODE_ROLLCALL` |
| Socket.IO | WebSocket → `/schoolTimeTable` | `SELF_REGISTRATION_ROLLCALL` |
| ntf pubsub | Atmosphere WebSocket | All notifications |

#### Example: Fully automatic rollcall

```python
import asyncio
from tronclass import TronClassClient
from tronclass.auth import XMULogin

client = TronClassClient("https://lnt.xmu.edu.cn", XMULogin("u", "p"))
listener = client.push_listener()

@listener.on_rollcall
def handle(rollcall):
    print(f"[{rollcall.rollcall_type}] {rollcall.course_title}")
    result = client.rollcall.auto_answer(rollcall)
    print("→", result)

@listener.on_notification
def notify(msg):
    print("Notification:", msg)

asyncio.run(listener.listen())
```

#### FCM state persistence

FCM registration state (android_id, security_token, FCM token, OneSignal player_id) is cached at `~/.tronclass_fcm_state.json` to avoid re-registering on every run.

---

## Exceptions

All exceptions are in `tronclass.exceptions`:

```python
from tronclass.exceptions import (
    TronClassError,              # Base exception
    AuthError,                   # 401 — not logged in / session expired
    PermissionError,             # 403 — access denied
    NotFoundError,               # 404 — resource not found
    RollcallError,               # Rollcall operation failed
    RollcallExpiredError,        # Rollcall already closed
    RollcallAlreadyAnsweredError, # Already submitted answer
    PushError,                   # Push channel error
)
```

Example:

```python
from tronclass.exceptions import RollcallAlreadyAnsweredError, RollcallExpiredError

try:
    client.rollcall.auto_answer(rc)
except RollcallAlreadyAnsweredError:
    print("Already answered!")
except RollcallExpiredError:
    print("Too late, rollcall closed.")
```

---

## Data Models

All API methods return typed dataclasses from `tronclass.models`:

```python
from tronclass.models import User, Course, Activity, Rollcall, Homework, Topic, Notification
```

Key properties:

```python
# Rollcall
rc.rollcall_id     # int
rc.rollcall_type   # "NUMBER_ROLLCALL" | "RADAR_ROLLCALL" | "QRCODE_ROLLCALL" | ...
rc.is_answered     # bool
rc.is_expired      # bool
rc.course_title    # str

# Course
course.course_id   # int
course.title       # str
course.teacher_name # str
course.term        # str
```

---

## Notes

- **XMU-specific:** The SDK is developed and tested against `lnt.xmu.edu.cn`. Other TronClass deployments should work with `TokenLogin` but may have slight API differences.
- **Radar rollcall:** Two-circle triangulation works reliably when you have at least two different location measurements from nearby points. The SDK uses classroom distances published in `/api/rollcall/{id}`.
- **NUMBER rollcall brute-force:** Sends 200 concurrent requests via `aiohttp`. Completes in under 5 seconds on typical connections.
- **QR rollcall:** The QR payload is extracted from the camera scan. If using a webcam or phone, pass the decoded string to `answer_qrcode()`.

---

## Project Structure

```
xmu-tronclass-sdk/
├── tronclass/
│   ├── __init__.py          # Exports TronClassClient, auth classes, exceptions
│   ├── client.py            # TronClassClient
│   ├── models.py            # User, Course, Activity, Rollcall, Homework, Topic, Notification
│   ├── exceptions.py        # Exception hierarchy
│   ├── auth/
│   │   ├── base.py          # BaseLogin ABC, TokenLogin
│   │   └── xmu.py           # XMULogin (AES OAuth2)
│   └── api/
│       ├── __init__.py      # APINamespace base
│       ├── profile.py
│       ├── courses.py
│       ├── rollcall.py
│       ├── assignments.py
│       ├── forum.py
│       ├── notifications.py
│       ├── activities.py
│       └── push.py          # PushListener (FCM + Socket.IO + ntf-WS)
├── examples/
│   ├── basic_usage.py
│   └── listen_push.py
└── pyproject.toml
```
