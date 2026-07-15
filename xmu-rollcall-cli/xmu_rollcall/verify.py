import uuid
import time
import math
import requests

base_url = "https://lnt.xmu.edu.cn"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://ids.xmu.edu.cn/authserver/login",
}

SIGNED_ATTENDANCE_STATUSES = {"on_call", "on_call_fine"}


def fetch_rollcall_details(in_session, rollcall_id):
    """Fetch the rollcall detail payload used for attendance and number codes."""
    url = f"{base_url}/api/rollcall/{rollcall_id}/student_rollcalls"
    try:
        response = in_session.get(url, headers=in_session.headers, timeout=15)
        if response.status_code != 200:
            print(f"Failed to get attendance status. HTTP {response.status_code}.")
            return None
        payload = response.json()
        if not isinstance(payload, dict):
            print("Failed to get attendance status. Unexpected response format.")
            return None
        return payload
    except (requests.RequestException, ValueError) as exc:
        print(f"Failed to get attendance status: {exc}")
        return None


def calculate_attendance_progress(data):
    """Return ``(signed, total, ratio)`` for a student_rollcalls response."""
    if not isinstance(data, dict):
        return None
    students = data.get("student_rollcalls")
    if not isinstance(students, list) or not students:
        return None

    signed = sum(
        1
        for student in students
        if isinstance(student, dict)
        and str(student.get("status", "")).lower() in SIGNED_ATTENDANCE_STATUSES
    )
    total = len(students)
    return signed, total, signed / total


def attendance_threshold_reached(in_session, rollcall_id, threshold):
    """Check whether enough classmates have answered.

    The detail payload is returned as the second value so number rollcalls can
    reuse it instead of immediately querying the same endpoint again.
    """
    if threshold <= 0:
        return True, None

    details = fetch_rollcall_details(in_session, rollcall_id)
    progress = calculate_attendance_progress(details)
    if progress is None:
        print("Attendance progress is unavailable; waiting before answering.")
        return False, details

    signed, total, ratio = progress
    if ratio < threshold:
        print(
            f"Waiting for attendance threshold: {signed}/{total} "
            f"({ratio:.0%}), target {threshold:.0%}."
        )
        return False, details

    print(
        f"Attendance threshold reached: {signed}/{total} "
        f"({ratio:.0%}), target {threshold:.0%}."
    )
    return True, details

def find_number_code(data, depth=0, max_depth=10):
    """Extract number_code from nested dict/list API responses.

    Args:
        data: Parsed JSON payload from Tronclass APIs.
        depth: Current recursive depth when traversing nested structures.
        max_depth: Maximum depth allowed for traversal to avoid pathological recursion.

    Returns:
        str or None: The first discovered number_code value, or None if not found.
    """
    if depth > max_depth:
        return None
    if isinstance(data, dict):
        number_code = data.get("number_code")
        if number_code is not None:
            return str(number_code)
        for value in data.values():
            nested_code = find_number_code(value, depth + 1, max_depth)
            if nested_code:
                return nested_code
    elif isinstance(data, list):
        for item in data:
            nested_code = find_number_code(item, depth + 1, max_depth)
            if nested_code:
                return nested_code
    return None

def send_code(in_session, rollcall_id, rollcall_details=None):
    answer_url = f"{base_url}/api/rollcall/{rollcall_id}/answer_number_rollcall"
    print("Trying number code from API...")
    t00 = time.time()
    request_headers = in_session.headers
    code_data = rollcall_details or fetch_rollcall_details(in_session, rollcall_id)
    if code_data is None:
        t01 = time.time()
        print(f"Failed to get number code.\nTime: {t01 - t00:.2f} s.")
        return False

    number_code = find_number_code(code_data)
    if not number_code:
        t01 = time.time()
        print(f"Failed to get number code. 'number_code' not found in API response.\nTime: {t01 - t00:.2f} s.")
        return False

    payload = {
        "deviceId": str(uuid.uuid4()),
        "numberCode": number_code
    }
    try:
        response = in_session.put(
            answer_url,
            json=payload,
            headers=request_headers,
            timeout=15,
        )
        if response.status_code == 200:
            print("Number code rollcall answered successfully.\nNumber code: ", number_code)
            time.sleep(5)
            t01 = time.time()
            print(f"Time: {t01 - t00:.2f} s.")
            return True
        t01 = time.time()
        print(f"Failed to submit number code. Status: {response.status_code}\nTime: {t01 - t00:.2f} s.")
        return False
    except requests.RequestException as e:
        t01 = time.time()
        print(f"Failed to submit number code: {e}\nTime: {t01 - t00:.2f} s.")
        return False


def send_self_registration(in_session, rollcall_id):
    """Answer a manual self-registration rollcall."""
    url = f"{base_url}/api/rollcall/{rollcall_id}/answer_self_registration_rollcall"
    payload = {"deviceId": str(uuid.uuid4())}
    try:
        response = in_session.put(url, json=payload, headers=in_session.headers, timeout=15)
    except requests.RequestException as exc:
        print(f"Failed to submit self-registration rollcall: {exc}")
        return False

    if response.status_code == 200:
        print("Self-registration rollcall answered successfully.")
        return True

    print(f"Failed to submit self-registration rollcall. HTTP {response.status_code}.")
    return False

def send_radar(in_session, rollcall_id):
    url = f"{base_url}/api/rollcall/{rollcall_id}/answer"

    lat_1, lat_2 = 24.3, 24.6
    lon_1, lon_2 = 118.0, 118.2

    def payload(lat, lon):
        return {
            "accuracy": 35,
            "altitude": 0,
            "altitudeAccuracy": None,
            "deviceId": str(uuid.uuid4()),
            "heading": None,
            "latitude": lat,
            "longitude": lon,
            "speed": None
        }

    res_1 = in_session.put(url, json=payload(lat_1, lon_1), headers=headers)
    data_1 = res_1.json()

    if res_1.status_code == 200:
        return True

    res_2 = in_session.put(url, json=payload(lat_2, lon_2), headers=headers)
    data_2 = res_2.json()

    if res_2.status_code == 200:
        return True

    distance_1 = data_1.get("distance")
    distance_2 = data_2.get("distance")

    def latlon_to_xy(lat, lon, lat0, lon0):
        R = 6371000
        x = math.radians(lon - lon0) * R * math.cos(math.radians(lat0))
        y = math.radians(lat - lat0) * R
        return x, y

    def xy_to_latlon(x, y, lat0, lon0):
        R = 6371000
        lat = lat0 + math.degrees(y / R)
        lon = lon0 + math.degrees(x / (R * math.cos(math.radians(lat0))))
        return lat, lon

    def circle_intersections(x1, y1, d1, x2, y2, d2):
        D = math.hypot(x2 - x1, y2 - y1)

        if D > d1 + d2 or D < abs(d1 - d2):
            return None

        a = (d1**2 - d2**2 + D**2) / (2 * D)
        h = math.sqrt(d1**2 - a**2)

        xm = x1 + a * (x2 - x1) / D
        ym = y1 + a * (y2 - y1) / D

        rx = -(y2 - y1) * (h / D)
        ry = (x2 - x1) * (h / D)

        p1 = (xm + rx, ym + ry)
        p2 = (xm - rx, ym - ry)
        return p1, p2

    def solve_two_points(lat1, lon1, lat2, lon2, d1, d2):
        lat0 = (lat1 + lat2) / 2
        lon0 = (lon1 + lon2) / 2
        x1, y1 = latlon_to_xy(lat1, lon1, lat0, lon0)
        x2, y2 = latlon_to_xy(lat2, lon2, lat0, lon0)

        sols = circle_intersections(x1, y1, d1, x2, y2, d2)
        if sols is None:
            return None

        p1 = xy_to_latlon(sols[0][0], sols[0][1], lat0, lon0)
        p2 = xy_to_latlon(sols[1][0], sols[1][1], lat0, lon0)
        return p1, p2

    resolutions = solve_two_points(lat_1, lon_1, lat_2, lon_2, distance_1, distance_2)
    if resolutions:
        ((sol_x_1, sol_y_1), (sol_x_2, sol_y_2)) = resolutions
    else:
        return False

    payload_1 = payload(sol_x_1, sol_y_1)
    payload_2 = payload(sol_x_2, sol_y_2)

    res_3 = in_session.put(url, json=payload_1, headers=headers)
    if res_3.status_code == 200:
        return True
    else:
        print(res_3.json())
        res_4 = in_session.put(url, json=payload_2, headers=headers)
        if res_4.status_code == 200:
            return True

    return False
