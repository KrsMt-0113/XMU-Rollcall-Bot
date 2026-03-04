"""Flask bridge server — exposes XMU-Tronclass-SDK as a local REST API.

Spawned by Electron main process; listens on localhost:47325.
All state (TronClassClient instance, push listener thread) is module-level.
"""

import asyncio
import json
import sys
import os
import threading
from dataclasses import asdict
from typing import Optional

from flask import Flask, jsonify, request
from flask_cors import CORS

# Locate the SDK relative to this file: ../../xmu-tronclass-sdk
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SDK = os.path.join(_ROOT, "xmu-tronclass-sdk")
if _SDK not in sys.path:
    sys.path.insert(0, _SDK)

from tronclass import TronClassClient
from tronclass.auth import XMULogin, TokenLogin
from tronclass.exceptions import TronClassError, AuthError

app = Flask(__name__)
CORS(app)

_client: Optional[TronClassClient] = None
_push_thread: Optional[threading.Thread] = None
_push_running = False
_push_loop: Optional[asyncio.AbstractEventLoop] = None
_push_events: list = []  # ring buffer of recent push events


def _ok(data=None, **kwargs):
    return jsonify({"ok": True, "data": data, **kwargs})


def _err(msg: str, code: int = 400):
    return jsonify({"ok": False, "error": msg}), code


def _require_client():
    if _client is None:
        return _err("Not logged in", 401)
    return None


# ── Auth ─────────────────────────────────────────────────────────────────────

@app.post("/login")
def login():
    global _client
    body = request.json or {}
    username = body.get("username", "").strip()
    password = body.get("password", "").strip()
    token = body.get("token", "").strip()
    base_url = body.get("base_url", "https://lnt.xmu.edu.cn").rstrip("/")

    if not username and not token:
        return _err("username or token required")

    try:
        if token:
            _client = TronClassClient(base_url, TokenLogin(token))
        else:
            _client = TronClassClient(base_url, XMULogin(username, password))
        me = _client.profile.me()
        return _ok({"user_id": _client.user_id, "name": me.name, "base_url": base_url})
    except AuthError as e:
        _client = None
        return _err(f"Login failed: {e}", 401)
    except Exception as e:
        _client = None
        return _err(f"Login error: {e}", 500)


@app.post("/logout")
def logout():
    global _client
    _stop_push()
    _client = None
    return _ok()


# ── Profile ───────────────────────────────────────────────────────────────────

@app.get("/profile")
def profile():
    if (e := _require_client()): return e
    try:
        me = _client.profile.me()
        return _ok(asdict(me))
    except Exception as e:
        return _err(str(e))


# ── Courses ───────────────────────────────────────────────────────────────────

@app.get("/courses")
def courses():
    if (e := _require_client()): return e
    try:
        semester_id = request.args.get("semester_id", type=int)
        academic_year_id = request.args.get("academic_year_id", type=int)
        data = [asdict(c) for c in _client.courses.list(
            semester_id=semester_id,
            academic_year_id=academic_year_id,
        )]
        return _ok(data)
    except Exception as e:
        return _err(str(e))


@app.get("/semesters")
def semesters():
    if (e := _require_client()): return e
    try:
        data = _client.courses.get_semesters()
        items = data if isinstance(data, list) else data.get("semesters", data.get("results", []))
        return _ok(items)
    except Exception as e:
        return _err(str(e))


@app.get("/courses/<int:course_id>")
def course_detail(course_id):
    if (e := _require_client()): return e
    try:
        course = asdict(_client.courses.get(course_id))
        return _ok(course)
    except Exception as e:
        return _err(str(e))


@app.get("/courses/<int:course_id>/activities")
def course_activities(course_id):
    if (e := _require_client()): return e
    try:
        acts = [asdict(a) for a in _client.courses.get_activities(course_id)]
        return _ok(acts)
    except Exception as e:
        return _err(str(e))


@app.get("/courses/<int:course_id>/bulletins")
def course_bulletins(course_id):
    if (e := _require_client()): return e
    try:
        items = _client.courses.get_bulletins(course_id)
        return _ok(items)
    except Exception as e:
        return _err(str(e))


@app.get("/courses/<int:course_id>/coursewares")
def course_coursewares(course_id):
    if (e := _require_client()): return e
    try:
        items = _client.courses.get_coursewares(course_id)
        return _ok(items)
    except Exception as e:
        return _err(str(e))


@app.get("/activities/<int:activity_id>/attachments")
def activity_attachments(activity_id):
    if (e := _require_client()): return e
    try:
        items = _client.courses.get_activity_attachments(activity_id)
        return _ok(items)
    except Exception as e:
        return _err(str(e))


@app.get("/attachments/<int:file_id>/url")
def attachment_url(file_id):
    if (e := _require_client()): return e
    try:
        url = _client.courses.get_attachment_url(file_id)
        return _ok({"url": url})
    except Exception as e:
        return _err(str(e))


# ── Rollcall ──────────────────────────────────────────────────────────────────

@app.get("/rollcall/active")
def rollcall_active():
    if (e := _require_client()): return e
    try:
        items = _client.rollcall.get_active()
        return _ok([asdict(r) for r in items])
    except Exception as e:
        return _err(str(e))


@app.post("/rollcall/answer")
def rollcall_answer():
    if (e := _require_client()): return e
    body = request.json or {}
    rollcall_id = body.get("rollcall_id")
    if not rollcall_id:
        return _err("rollcall_id required")
    try:
        active = _client.rollcall.get_active()
        target = next((r for r in active if r.rollcall_id == int(rollcall_id)), None)
        if not target:
            return _err(f"Rollcall {rollcall_id} not found in active list")
        result = _client.rollcall.auto_answer(target)
        return _ok(result)
    except Exception as e:
        return _err(str(e))


@app.post("/rollcall/answer_all")
def rollcall_answer_all():
    if (e := _require_client()): return e
    try:
        results = _client.rollcall.answer_all_active()
        return _ok(results)
    except Exception as e:
        return _err(str(e))


# ── Assignments ───────────────────────────────────────────────────────────────

@app.get("/assignments")
def assignments():
    if (e := _require_client()): return e
    try:
        data = [asdict(h) for h in _client.assignments.list_homework()]
        return _ok(data)
    except Exception:
        # Fallback: activities API filtered by type=homework
        try:
            raw = _client.activities.list_user_activities(activity_type="homework")
            items = raw if isinstance(raw, list) else raw.get("activities", raw.get("results", []))
            data = [{
                "id": item.get("id", 0),
                "title": item.get("title", item.get("name", "")),
                "course_id": item.get("course_id", 0),
                "due_at": item.get("due_at") or item.get("deadline"),
                "submitted": item.get("submitted", False),
                "score": item.get("score"),
            } for item in items]
            return _ok(data)
        except Exception as e2:
            return _err(str(e2))


# ── Notifications ─────────────────────────────────────────────────────────────

@app.get("/notifications")
def notifications():
    if (e := _require_client()): return e
    try:
        data = [asdict(n) for n in _client.notifications.list_alerts()]
        return _ok(data)
    except Exception as e:
        return _err(str(e))


# ── Push listener ─────────────────────────────────────────────────────────────

def _push_thread_fn():
    global _push_running, _push_loop
    _push_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_push_loop)
    _push_running = True

    listener = _client.push_listener()

    def _on_rollcall(rollcall):
        _push_events.append({"type": "rollcall", "data": asdict(rollcall)})
        if len(_push_events) > 50:
            _push_events.pop(0)
        # Auto-answer
        try:
            _client.rollcall.auto_answer(rollcall)
            _push_events.append({"type": "answered", "rollcall_id": rollcall.rollcall_id})
        except Exception as ex:
            _push_events.append({"type": "answer_failed", "rollcall_id": rollcall.rollcall_id, "error": str(ex)})

    def _on_notification(msg):
        _push_events.append({"type": "notification", "data": msg})
        if len(_push_events) > 50:
            _push_events.pop(0)

    listener.on_rollcall(_on_rollcall)
    listener.on_notification(_on_notification)

    try:
        _push_loop.run_until_complete(listener.listen())
    except Exception:
        pass
    finally:
        _push_running = False


def _stop_push():
    global _push_running, _push_loop, _push_thread
    _push_running = False
    if _push_loop and _push_loop.is_running():
        _push_loop.call_soon_threadsafe(_push_loop.stop)
    _push_thread = None
    _push_loop = None


@app.get("/push/status")
def push_status():
    return _ok({"running": _push_running, "events": _push_events[-20:]})


@app.post("/push/start")
def push_start():
    global _push_thread, _push_running
    if (e := _require_client()): return e
    if _push_running:
        return _ok({"running": True})
    _push_thread = threading.Thread(target=_push_thread_fn, daemon=True)
    _push_thread.start()
    return _ok({"running": True})


@app.post("/push/stop")
def push_stop():
    _stop_push()
    return _ok({"running": False})


@app.post("/push/events/clear")
def push_events_clear():
    _push_events.clear()
    return _ok()


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return _ok({"logged_in": _client is not None})


if __name__ == "__main__":
    port = int(os.environ.get("BRIDGE_PORT", "47325"))
    print(f"[bridge] Starting on port {port}", flush=True)
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
