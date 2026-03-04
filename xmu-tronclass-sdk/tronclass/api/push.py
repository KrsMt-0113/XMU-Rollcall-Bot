"""Push notification listener.

Listens on three parallel channels:
  1. FCM/OneSignal (MCS long connection) — NUMBER/RADAR/QRCODE rollcall (primary)
  2. Socket.IO /schoolTimeTable           — SELF_REGISTRATION rollcall
  3. ntf pubsub WebSocket (Atmosphere)    — generic notifications

Usage::

    listener = client.push_listener()

    @listener.on_rollcall
    def handle(rollcall):
        print(f"New rollcall: {rollcall.rollcall_type}")
        client.rollcall.auto_answer(rollcall)

    import asyncio
    asyncio.run(listener.listen())
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import ssl
import struct
import urllib.request
import urllib.parse
import urllib.error
from typing import Callable, List, Optional, TYPE_CHECKING

import websockets
import socketio

if TYPE_CHECKING:
    from ..client import TronClassClient
    from ..models import Rollcall

_ONESIGNAL_APP_ID = "c810be65-8ec7-4f73-a802-20862e93c9b8"
_FCM_SENDER_ID = "621033611809"
_FCM_CHECKIN_URL = "https://android.clients.google.com/checkin"
_FCM_REGISTER_URL = "https://android.clients.google.com/c2dm/register3"
_MCS_HOST = "mtalk.google.com"
_MCS_PORT = 5228
_FCM_STATE_FILE = os.path.expanduser("~/.tronclass_fcm_state.json")


# ── Minimal protobuf helpers ──────────────────────────────

def _pb_varint(v: int) -> bytes:
    out = b""
    v = int(v) & 0xFFFFFFFFFFFFFFFF
    while v > 0x7F:
        out += bytes([(v & 0x7F) | 0x80])
        v >>= 7
    return out + bytes([v])


def _pb_tag(field: int, wtype: int) -> bytes:
    return _pb_varint((field << 3) | wtype)


def _pb_f0(field: int, v: int) -> bytes:          # varint
    return _pb_tag(field, 0) + _pb_varint(v)


def _pb_f1(field: int, v: int) -> bytes:          # fixed64 LE
    return _pb_tag(field, 1) + struct.pack("<Q", int(v) & 0xFFFFFFFFFFFFFFFF)


def _pb_f2(field: int, b) -> bytes:               # length-delimited
    if isinstance(b, str):
        b = b.encode()
    return _pb_tag(field, 2) + _pb_varint(len(b)) + b


def _pb_decode(data: bytes) -> dict:
    res: dict = {}
    i, n = 0, len(data)
    while i < n:
        tag, shift = 0, 0
        while True:
            b = data[i]; i += 1
            tag |= (b & 0x7F) << shift; shift += 7
            if not (b & 0x80):
                break
        f, wt = tag >> 3, tag & 7
        if wt == 0:
            val, shift = 0, 0
            while True:
                b = data[i]; i += 1
                val |= (b & 0x7F) << shift; shift += 7
                if not (b & 0x80):
                    break
        elif wt == 1:
            val = struct.unpack_from("<Q", data, i)[0]; i += 8
        elif wt == 2:
            ln, shift = 0, 0
            while True:
                b = data[i]; i += 1
                ln |= (b & 0x7F) << shift; shift += 7
                if not (b & 0x80):
                    break
            val = bytes(data[i:i + ln]); i += ln
        elif wt == 5:
            val = struct.unpack_from("<I", data, i)[0]; i += 4
        else:
            break
        res.setdefault(f, []).append(val)
    return res


# ── FCM registration ──────────────────────────────────────

async def _fcm_checkin(android_id: int = 0, security_token: int = 0):
    chrome_build = _pb_f0(1, 2) + _pb_f2(2, "63.0.3234.0") + _pb_f0(3, 1)
    checkin = _pb_f2(9, chrome_build) + _pb_f0(11, 3)
    body = (
        _pb_f0(2, android_id) + _pb_f2(4, checkin)
        + _pb_f1(13, security_token) + _pb_f0(14, 3) + _pb_f0(22, 0)
    )
    req = urllib.request.Request(
        _FCM_CHECKIN_URL, data=body,
        headers={"Content-Type": "application/x-protobuf"},
    )
    resp_data = urllib.request.urlopen(req, timeout=15).read()
    parsed = _pb_decode(resp_data)
    return parsed.get(7, [0])[0], parsed.get(8, [0])[0]


async def _fcm_register(android_id: int, security_token: int) -> str:
    data = urllib.parse.urlencode({
        "app": "org.chromium.linux",
        "X-subtype": _FCM_SENDER_ID,
        "device": str(android_id),
        "sender": _FCM_SENDER_ID,
    }).encode()
    req = urllib.request.Request(
        _FCM_REGISTER_URL, data=data,
        headers={
            "Authorization": f"AidLogin {android_id}:{security_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    text = urllib.request.urlopen(req, timeout=15).read().decode()
    if "token=" in text:
        return text.split("token=")[1].strip()
    raise RuntimeError(f"FCM register failed: {text}")


async def _onesignal_create_player(fcm_token: str) -> str:
    payload = json.dumps({
        "app_id": _ONESIGNAL_APP_ID,
        "device_type": 1,
        "identifier": fcm_token,
        "language": "zh-Hans",
        "timezone": 28800,
        "device_model": "Linux",
        "device_os": "10",
        "sdk": "030803",
    }).encode()
    req = urllib.request.Request(
        "https://onesignal.com/api/v1/players", data=payload,
        headers={"Content-Type": "application/json"},
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return resp["id"]


async def _onesignal_update_player(player_id: str, external_user_id: str, tags: list):
    """Send external_user_id + tags in batches of 100."""
    tag_items = [(str(t), "1") for t in tags]

    def _put(payload_dict):
        payload = json.dumps(payload_dict).encode()
        req = urllib.request.Request(
            f"https://onesignal.com/api/v1/players/{player_id}",
            data=payload, method="PUT",
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=15).read()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}")

    batch = dict(tag_items[:100])
    _put({"app_id": _ONESIGNAL_APP_ID, "external_user_id": external_user_id, "tags": batch})
    for i in range(100, len(tag_items), 100):
        _put({"app_id": _ONESIGNAL_APP_ID, "tags": dict(tag_items[i:i + 100])})


# ── MCS helpers ───────────────────────────────────────────

def _mcs_login_request(android_id: int, security_token: int) -> bytes:
    setting = _pb_f2(1, "new_vc") + _pb_f2(2, "1")
    return (
        _pb_f2(1, "chrome-63.0.3234.0")
        + _pb_f2(2, "mcs.android.com")
        + _pb_f2(3, str(android_id))
        + _pb_f2(4, str(android_id))
        + _pb_f2(5, str(security_token))
        + _pb_f2(6, f"android-{android_id:x}")
        + _pb_f2(8, setting)
        + _pb_f0(11, 2)
        + _pb_f0(13, 0)
        + _pb_f0(14, 1)
        + _pb_f0(17, 1)
    )


async def _mcs_read_msg(reader: asyncio.StreamReader):
    tag = (await reader.readexactly(1))[0]
    ln, shift = 0, 0
    while True:
        b = (await reader.readexactly(1))[0]
        ln |= (b & 0x7F) << shift; shift += 7
        if not (b & 0x80):
            break
    body = await reader.readexactly(ln) if ln else b""
    return tag, body


# ── PushListener ─────────────────────────────────────────

class PushListener:
    """Concurrent push notification listener for TronClass.

    Handles three channels simultaneously:

    - **FCM/MCS** (``mtalk.google.com:5228``) — NUMBER, RADAR, QRCODE rollcalls
    - **Socket.IO** (``/schoolTimeTable``) — self-registration rollcalls
    - **ntf WebSocket** (Atmosphere protocol) — generic notifications

    Args:
        client: Authenticated :class:`~tronclass.client.TronClassClient`.

    Example::

        listener = client.push_listener()

        @listener.on_rollcall
        def handle(rollcall):
            result = client.rollcall.auto_answer(rollcall)
            print("Answered:", result)

        @listener.on_notification
        def notify(msg):
            print("Notification:", msg)

        import asyncio
        asyncio.run(listener.listen())
    """

    def __init__(self, client: "TronClassClient"):
        self._client = client
        self._rollcall_handlers: List[Callable] = []
        self._notification_handlers: List[Callable] = []

    def on_rollcall(self, fn: Callable) -> Callable:
        """Register a callback for rollcall push events.

        The callback receives a :class:`~tronclass.models.Rollcall` instance.

        Can be used as a decorator::

            @listener.on_rollcall
            def handle(rollcall):
                client.rollcall.auto_answer(rollcall)
        """
        self._rollcall_handlers.append(fn)
        return fn

    def on_notification(self, fn: Callable) -> Callable:
        """Register a callback for generic notification events.

        The callback receives a raw dict from the ntf WebSocket.

        Can be used as a decorator::

            @listener.on_notification
            def handle(msg):
                print(msg)
        """
        self._notification_handlers.append(fn)
        return fn

    async def listen(self):
        """Start all three push channels concurrently.

        This coroutine runs forever (until cancelled). Use with::

            asyncio.run(listener.listen())

        Or alongside other coroutines::

            await asyncio.gather(listener.listen(), your_other_task())
        """
        await asyncio.gather(
            self._listen_fcm(),
            self._listen_socketio(),
            self._listen_ntf(),
        )

    # ── Dispatch helpers ─────────────────────────────────

    def _dispatch_rollcall(self, rollcall_data: dict, rollcall_type: str):
        from ..models import Rollcall
        # Build a minimal Rollcall object from push data
        rc = Rollcall(
            rollcall_id=rollcall_data.get("rollcall_id") or rollcall_data.get("id", 0),
            course_title=rollcall_data.get("course_title", ""),
            created_by_name=rollcall_data.get("created_by_name", ""),
            department_name=rollcall_data.get("department_name", ""),
            is_number=rollcall_type == "NUMBER_ROLLCALL",
            is_radar=rollcall_type == "RADAR_ROLLCALL",
            is_qrcode=rollcall_type == "QRCODE_ROLLCALL",
            is_expired=False,
            status="absent",
            rollcall_status="rollcalling",
            scored=False,
            raw=rollcall_data,
        )
        loop = asyncio.get_event_loop()
        for fn in self._rollcall_handlers:
            try:
                if asyncio.iscoroutinefunction(fn):
                    loop.create_task(fn(rc))
                else:
                    loop.run_in_executor(None, fn, rc)
            except Exception as e:
                print(f"[Push] handler error: {e}")

    def _dispatch_notification(self, msg: dict):
        loop = asyncio.get_event_loop()
        for fn in self._notification_handlers:
            try:
                if asyncio.iscoroutinefunction(fn):
                    loop.create_task(fn(msg))
                else:
                    loop.run_in_executor(None, fn, msg)
            except Exception as e:
                print(f"[Push] notification handler error: {e}")

    # ── Channel 1: FCM/MCS ───────────────────────────────

    async def _listen_fcm(self):
        alias = f"XMU_user_{self._client.user_id}_lang_en_us"
        state: dict = {}
        if os.path.exists(_FCM_STATE_FILE):
            try:
                state = json.loads(open(_FCM_STATE_FILE).read())
            except Exception:
                pass

        android_id = state.get("android_id", 0)
        security_token = state.get("security_token", 0)
        fcm_token = state.get("fcm_token")
        player_id = state.get("player_id")

        def _save():
            with open(_FCM_STATE_FILE, "w") as f:
                json.dump({
                    "android_id": android_id, "security_token": security_token,
                    "fcm_token": fcm_token, "player_id": player_id,
                }, f)

        # Step 1: checkin
        try:
            android_id, security_token = await _fcm_checkin(android_id, security_token)
            print(f"[FCM] Checkin ok: android_id={android_id}")
        except Exception as e:
            print(f"[FCM] Checkin failed: {e}")

        # Step 2: register
        if not fcm_token:
            try:
                fcm_token = await _fcm_register(android_id, security_token)
                print(f"[FCM] Registered: token={fcm_token[:32]}...")
            except Exception as e:
                print(f"[FCM] Register failed: {e}")

        # Step 3: OneSignal player
        if fcm_token and not player_id:
            try:
                player_id = await _onesignal_create_player(fcm_token)
                print(f"[OneSignal] Player created: {player_id}")
            except Exception as e:
                print(f"[OneSignal] Create player failed: {e}")

        if android_id and fcm_token and player_id:
            _save()

        # Step 4: set external_user_id + tags
        if player_id:
            try:
                tags_data = self._client._get("/api/user/tags")
                tags = tags_data.get("tags", [])
                await _onesignal_update_player(player_id, alias, tags)
                print(f"[OneSignal] Player updated: {alias}, {len(tags)} tags")
            except Exception as e:
                print(f"[OneSignal] Player update failed: {e}")

        if not android_id or not security_token:
            print("[FCM] Cannot connect to MCS: checkin failed")
            return

        # Step 5: MCS long connection
        while True:
            writer = None
            try:
                ssl_ctx = ssl.create_default_context()
                reader, writer = await asyncio.open_connection(_MCS_HOST, _MCS_PORT, ssl=ssl_ctx)
                print(f"[MCS] Connected to {_MCS_HOST}:{_MCS_PORT}")

                login_body = _mcs_login_request(android_id, security_token)
                writer.write(bytes([41, 2]) + _pb_varint(len(login_body)) + login_body)
                await writer.drain()
                await reader.read(1)  # server version byte

                while True:
                    try:
                        tag, body = await asyncio.wait_for(_mcs_read_msg(reader), timeout=300)
                    except asyncio.TimeoutError:
                        writer.write(bytes([0, 0]))  # HeartbeatPing
                        await writer.drain()
                        continue

                    if tag == 3:   # LoginResponse
                        resp = _pb_decode(body)
                        print(f"[MCS] LoginResponse: id={resp.get(1, [b'?'])[0]}")
                    elif tag == 8:  # DataMessageStanza — push notification
                        self._handle_mcs_data(body)
                    elif tag == 0:  # HeartbeatPing from server
                        writer.write(bytes([1, 0]))
                        await writer.drain()
                    elif tag == 4:  # Close
                        print("[MCS] Server closed connection")
                        break

            except (OSError, asyncio.IncompleteReadError) as e:
                print(f"[MCS] Connection error: {e}, reconnecting in 10s...")
                await asyncio.sleep(10)
            except Exception as e:
                print(f"[MCS] Error: {e}, reconnecting in 10s...")
                await asyncio.sleep(10)
            finally:
                if writer:
                    try:
                        writer.close()
                    except Exception:
                        pass

    def _handle_mcs_data(self, body: bytes):
        msg = _pb_decode(body)
        app_data: dict = {}
        for ad_bytes in msg.get(6, []):
            ad = _pb_decode(ad_bytes)
            k = ad.get(1, [b""])[0]
            v = ad.get(2, [b""])[0]
            if isinstance(k, bytes):
                k = k.decode("utf-8", errors="replace")
            if isinstance(v, bytes):
                v = v.decode("utf-8", errors="replace")
            app_data[k] = v

        custom_raw = app_data.get("custom", "")
        if not custom_raw:
            return
        try:
            custom = json.loads(custom_raw)
            additional = custom.get("a", {})
            msg_type = additional.get("message", "")
            if msg_type in ("NUMBER_ROLLCALL", "RADAR_ROLLCALL", "QRCODE_ROLLCALL"):
                print(f"[FCM] Rollcall push: {msg_type}")
                self._dispatch_rollcall(additional, msg_type)
        except Exception as e:
            print(f"[MCS] Parse error: {e}")

    # ── Channel 2: Socket.IO ─────────────────────────────

    async def _listen_socketio(self):
        session_id = self._client.session_id
        sio = socketio.AsyncClient(
            reconnection=True, reconnection_attempts=0,
            reconnection_delay=3, logger=False, engineio_logger=False,
        )

        @sio.event(namespace="/schoolTimeTable")
        async def connect():
            print("[Socket.IO] Connected to /schoolTimeTable")

        @sio.event(namespace="/schoolTimeTable")
        async def disconnect():
            print("[Socket.IO] Disconnected from /schoolTimeTable")

        @sio.on("self_registration_rollcall_start", namespace="/schoolTimeTable")
        async def on_self_reg(data):
            print(f"[Socket.IO] self_registration_rollcall_start: {data}")
            self._dispatch_rollcall(data, "SELF_REGISTRATION_ROLLCALL")

        while True:
            try:
                await sio.connect(
                    self._client.base_url,
                    namespaces=["/schoolTimeTable"],
                    headers={"X-SESSION-ID": session_id},
                    transports=["websocket"],
                    wait_timeout=10,
                )
                await sio.wait()
            except Exception as e:
                print(f"[Socket.IO] Error: {e}, reconnecting in 5s...")
                await asyncio.sleep(5)

    # ── Channel 3: ntf WebSocket (Atmosphere) ────────────

    async def _listen_ntf(self):
        session_id = self._client.session_id
        user_id = self._client.user_id
        url = (
            f"wss://{self._client.base_url.split('://', 1)[-1]}"
            f"/ntf/pubsub/{user_id}"
            f"?X-Atmosphere-tracking-id=0"
            f"&X-Atmosphere-Transport=websocket"
            f"&Content-Type=application%2Fjson"
            f"&X-atmo-protocol=true"
            f"&X-SESSION-ID={session_id}"
        )
        while True:
            try:
                async with websockets.connect(
                    url,
                    additional_headers={"X-SESSION-ID": session_id},
                    ping_interval=None,
                    open_timeout=10,
                ) as ws:
                    print("[ntf] Connected to pubsub")
                    async for raw in ws:
                        parts = raw.split("|", 3)
                        if len(parts) < 4 or not parts[3]:
                            continue
                        try:
                            msg = json.loads(parts[3])
                        except (json.JSONDecodeError, ValueError):
                            continue
                        msg_type = msg.get("type", "")
                        if "rollcall" in msg_type.lower():
                            self._dispatch_rollcall(msg, msg_type.upper())
                        else:
                            self._dispatch_notification(msg)
            except Exception as e:
                print(f"[ntf] Disconnected: {e}, reconnecting in 5s...")
                await asyncio.sleep(5)
