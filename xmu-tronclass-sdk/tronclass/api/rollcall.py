"""Rollcall (attendance) API — the most important module.

Implements:
- Fetching active rollcalls
- Answering NUMBER rollcall (brute-force 0000–9999 concurrently)
- Answering RADAR rollcall (two-point geolocation triangulation)
- Answering QRCODE rollcall (QR payload submission)
- auto_answer() that detects type and handles everything automatically
"""

import asyncio
import math
import time
import uuid
from typing import List, Optional, Callable, Tuple

import aiohttp
from aiohttp import CookieJar

from . import APINamespace
from ..models import Rollcall
from ..exceptions import RollcallError, RollcallExpiredError, RollcallAlreadyAnsweredError


class RollcallAPI(APINamespace):
    """Rollcall (attendance check) operations.

    Access via ``client.rollcall``.
    """

    def get_active(self) -> List[Rollcall]:
        """Return all currently active rollcalls for the user.

        Returns:
            List of :class:`~tronclass.models.Rollcall` (may be empty).
        """
        data = self._get("/api/radar/rollcalls")
        raw_list = data.get("rollcalls", [])
        return [Rollcall.from_dict(r) for r in raw_list]

    def get(self, rollcall_id: int) -> dict:
        """Return full details of a specific rollcall by ID."""
        return self._get(f"/api/rollcall/{rollcall_id}")

    def answer_number(self, rollcall_id: int, number_code: str) -> dict:
        """Submit a specific number code for a NUMBER rollcall.

        Args:
            rollcall_id: The rollcall ID.
            number_code: 4-digit code as string (e.g. ``"0042"``).

        Raises:
            RollcallError: If the code was rejected.
        """
        return self._put(
            f"/api/rollcall/{rollcall_id}/answer_number_rollcall",
            json={"deviceId": str(uuid.uuid4()), "numberCode": number_code},
        )

    def answer_radar(
        self,
        rollcall_id: int,
        latitude: float,
        longitude: float,
        accuracy: float = 35.0,
    ) -> dict:
        """Submit a location for a RADAR rollcall.

        Args:
            rollcall_id: The rollcall ID.
            latitude: GPS latitude.
            longitude: GPS longitude.
            accuracy: Location accuracy in metres (default 35).

        Returns:
            API response dict. If out of range, includes ``distance`` field.
        """
        return self._put(
            f"/api/rollcall/{rollcall_id}/answer",
            json={
                "accuracy": accuracy,
                "altitude": 0,
                "altitudeAccuracy": None,
                "deviceId": str(uuid.uuid4()),
                "heading": None,
                "latitude": latitude,
                "longitude": longitude,
                "speed": None,
            },
        )

    def answer_qrcode(self, rollcall_id: int, qr_payload: str) -> dict:
        """Submit a QR code payload for a QRCODE rollcall.

        Args:
            rollcall_id: The rollcall ID.
            qr_payload: Raw text decoded from the QR code.
        """
        return self._put(
            f"/api/rollcall/{rollcall_id}/answer_qr_rollcall",
            json={"deviceId": str(uuid.uuid4()), "qrCode": qr_payload},
        )

    def get_merged_rollcall(self) -> dict:
        """Return merged rollcall (combined attendance view)."""
        return self._get("/api/rollcall/merged-rollcall")

    def get_student_rollcalls(self, rollcall_id: int) -> List[dict]:
        """Return student rollcall records for a merged rollcall."""
        return self._get(f"/api/rollcall/merged-rollcall/{rollcall_id}/student-rollcalls")

    # ── High-level helpers ──────────────────────────────────

    def brute_force_number(
        self,
        rollcall_id: int,
        concurrency: int = 200,
        timeout: float = 5.0,
        on_progress: Optional[Callable[[int], None]] = None,
    ) -> Optional[str]:
        """Brute-force a NUMBER rollcall by trying all 0000–9999 codes concurrently.

        Args:
            rollcall_id: The rollcall ID.
            concurrency: Max simultaneous requests (default 200).
            timeout: Per-request timeout in seconds.
            on_progress: Optional callback called with the current attempt number.

        Returns:
            The winning code as a string (e.g. ``"0042"``), or ``None`` if all failed.
        """
        url = f"{self._client.base_url}/api/rollcall/{rollcall_id}/answer_number_rollcall"
        session = self._client._session

        async def _run():
            stop = asyncio.Event()
            sem = asyncio.Semaphore(concurrency)
            jar = CookieJar()
            for c in session.cookies:
                jar.update_cookies({c.name: c.value})
            result: List[Optional[str]] = [None]

            async def try_code(code: str):
                if stop.is_set():
                    return
                async with sem:
                    if stop.is_set():
                        return
                    payload = {"deviceId": str(uuid.uuid4()), "numberCode": code}
                    try:
                        async with aio_session.put(
                            url, json=payload,
                            timeout=aiohttp.ClientTimeout(total=timeout)
                        ) as r:
                            if r.status == 200:
                                stop.set()
                                result[0] = code
                    except Exception:
                        pass
                    if on_progress:
                        on_progress(int(code))

            async with aiohttp.ClientSession(
                headers=dict(session.headers), cookie_jar=jar
            ) as aio_session:
                tasks = [
                    asyncio.create_task(try_code(str(i).zfill(4)))
                    for i in range(10000)
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
            return result[0]

        return asyncio.run(_run())

    def triangulate_radar(
        self,
        rollcall_id: int,
        probe_points: Optional[List[Tuple[float, float]]] = None,
    ) -> bool:
        """Attempt RADAR rollcall using two-point geolocation triangulation.

        Sends two probe requests to measure distance from the check-in point,
        then solves the two-circle intersection to find valid coordinates.

        Args:
            rollcall_id: The rollcall ID.
            probe_points: List of (lat, lon) tuples to use as probes.
                          Defaults to two points around XMU Xiang'an campus.

        Returns:
            ``True`` if successfully answered, ``False`` otherwise.
        """
        if probe_points is None:
            # Default: two points around XMU Xiang'an campus
            probe_points = [(24.3, 118.0), (24.6, 118.2)]

        def mk_payload(lat, lon):
            return {
                "accuracy": 35, "altitude": 0, "altitudeAccuracy": None,
                "deviceId": str(uuid.uuid4()), "heading": None,
                "latitude": lat, "longitude": lon, "speed": None,
            }

        url = f"/api/rollcall/{rollcall_id}/answer"
        lat1, lon1 = probe_points[0]
        lat2, lon2 = probe_points[1]

        r1 = self._put(url, json=mk_payload(lat1, lon1))
        if r1.get("status_code") == 200 or "rollcall_id" in r1:
            return True

        r2 = self._put(url, json=mk_payload(lat2, lon2))
        if r2.get("status_code") == 200 or "rollcall_id" in r2:
            return True

        d1 = r1.get("distance")
        d2 = r2.get("distance")
        if d1 is None or d2 is None:
            return False

        solutions = _solve_two_circles(lat1, lon1, d1, lat2, lon2, d2)
        if solutions is None:
            return False

        for sol_lat, sol_lon in solutions:
            resp = self._put(url, json=mk_payload(sol_lat, sol_lon))
            if "rollcall_id" in resp or resp.get("success"):
                return True
        return False

    def auto_answer(self, rollcall: Rollcall, **kwargs) -> bool:
        """Automatically detect rollcall type and answer it.

        Dispatches to :meth:`brute_force_number`, :meth:`triangulate_radar`,
        or raises ``RollcallError`` for unsupported types.

        Args:
            rollcall: A :class:`~tronclass.models.Rollcall` instance.
            **kwargs: Passed through to the specific answer method.

        Returns:
            ``True`` on success.

        Raises:
            RollcallAlreadyAnsweredError: If already answered.
            RollcallExpiredError: If the rollcall has expired.
            RollcallError: For unsupported rollcall types or failures.
        """
        if rollcall.is_answered:
            raise RollcallAlreadyAnsweredError(
                f"Rollcall {rollcall.rollcall_id} is already answered."
            )
        if rollcall.is_expired:
            raise RollcallExpiredError(
                f"Rollcall {rollcall.rollcall_id} has expired."
            )

        if rollcall.is_number:
            code = self.brute_force_number(rollcall.rollcall_id, **kwargs)
            return code is not None
        elif rollcall.is_radar:
            return self.triangulate_radar(rollcall.rollcall_id, **kwargs)
        else:
            raise RollcallError(
                f"QRCODE rollcall {rollcall.rollcall_id} requires a QR code — "
                "use answer_qrcode() after scanning."
            )

    def answer_all_active(self, **kwargs) -> dict:
        """Fetch all active rollcalls and auto-answer each one.

        Returns:
            dict mapping rollcall_id → True/False/exception.
        """
        rollcalls = self.get_active()
        results = {}
        for rc in rollcalls:
            try:
                results[rc.rollcall_id] = self.auto_answer(rc, **kwargs)
            except Exception as e:
                results[rc.rollcall_id] = e
        return results


# ── Geometry helpers ──────────────────────────────────────

def _latlon_to_xy(lat, lon, lat0, lon0):
    R = 6_371_000
    x = math.radians(lon - lon0) * R * math.cos(math.radians(lat0))
    y = math.radians(lat - lat0) * R
    return x, y


def _xy_to_latlon(x, y, lat0, lon0):
    R = 6_371_000
    lat = lat0 + math.degrees(y / R)
    lon = lon0 + math.degrees(x / (R * math.cos(math.radians(lat0))))
    return lat, lon


def _solve_two_circles(lat1, lon1, d1, lat2, lon2, d2):
    """Find intersection points of two circles on Earth surface."""
    lat0 = (lat1 + lat2) / 2
    lon0 = (lon1 + lon2) / 2
    x1, y1 = _latlon_to_xy(lat1, lon1, lat0, lon0)
    x2, y2 = _latlon_to_xy(lat2, lon2, lat0, lon0)

    D = math.hypot(x2 - x1, y2 - y1)
    if D > d1 + d2 or D < abs(d1 - d2):
        return None

    a = (d1**2 - d2**2 + D**2) / (2 * D)
    h_sq = d1**2 - a**2
    if h_sq < 0:
        return None
    h = math.sqrt(h_sq)

    xm = x1 + a * (x2 - x1) / D
    ym = y1 + a * (y2 - y1) / D
    rx = -(y2 - y1) * (h / D)
    ry = (x2 - x1) * (h / D)

    p1 = _xy_to_latlon(xm + rx, ym + ry, lat0, lon0)
    p2 = _xy_to_latlon(xm - rx, ym - ry, lat0, lon0)
    return [p1, p2]
