import uuid
import time
import asyncio
import aiohttp
import math
from aiohttp import CookieJar

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

def pad(i):
    return str(i).zfill(4)

def send_code(in_session, rollcall_id):
    url = f"{base_url}/api/rollcall/{rollcall_id}/answer_number_rollcall"
    print("Trying number code...")
    t00 = time.time()

    async def put_request(i, session, stop_flag, answer_url, sem, timeout):
        if stop_flag.is_set():
            return None
        async with sem:
            if stop_flag.is_set():
                return None
            payload = {
                "deviceId": str(uuid.uuid4()),
                "numberCode": pad(i)
            }
            try:
                async with session.put(answer_url, json=payload) as r:
                    if r.status == 200:
                        stop_flag.set()
                        return pad(i)
            except Exception:
                pass
            return None

    async def main():
        stop_flag = asyncio.Event()
        sem = asyncio.Semaphore(200)
        timeout = aiohttp.ClientTimeout(total=5)
        cookie_jar = CookieJar()
        for c in in_session.cookies:
            cookie_jar.update_cookies({c.name: c.value})
        async with aiohttp.ClientSession(headers=in_session.headers, cookie_jar=cookie_jar) as session:
            tasks = [asyncio.create_task(put_request(i, session, stop_flag, url, sem, timeout)) for i in range(10000)]
            try:
                for coro in asyncio.as_completed(tasks):
                    res = await coro
                    if res is not None:
                        for t in tasks:
                            if not t.done():
                                t.cancel()
                        print("Number code rollcall answered successfully.\nNumber code: ", res)
                        time.sleep(5)
                        t01 = time.time()
                        print("Time: %.2f s." % (t01 - t00))
                        return True
            finally:
                # 确保所有 task 结束
                for t in tasks:
                    if not t.done():
                        t.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        t01 = time.time()
        print("Failed.\nTime: %.2f s." % (t01 - t00))
        return False

    return asyncio.run(main())

# def send_radar(in_session, rollcall_id):
#     url = f"{base_url}/api/rollcall/{rollcall_id}/answer?api_version=1.76"
#     print("Trying radar rollcall...")
#
#     payload = {
#         "accuracy": 35,
#         "altitude": 0,
#         "altitudeAccuracy": None,
#         "deviceId": str(uuid.uuid4()),
#         "heading": None,
#         "latitude": LATITUDE,
#         "longitude": LONGITUDE,
#         "speed": None
#     }
#
#     try:
#         response = in_session.put(url, json=payload, headers=headers)
#         if response.status_code == 200:
#             print("Radar rollcall success!")
#             return True
#         else:
#             print(f"Radar rollcall failed with status code: {response.status_code}")
#             return False
#     except Exception as e:
#         print(f"Error in send_radar: {e}")
#         return False

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
    res_2 = in_session.put(url, json=payload(lat_2, lon_2), headers=headers)
    data_2 = res_2.json()
    distance_1 = data_1["distance"]
    distance_2 = data_2["distance"]

    print(data_1, data_2)  # debug

    if res_1.status_code == 200 or res_2.status_code == 200:
        # print("[Debug] 预设位置签到成功。")  # debug
        # time.sleep(10)
        return True

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
        # print(f"[Debug] 解方程得到：{resolutions}")  # debug
    else:
        # print("[Debug] 无解。")   # debug
        # time.sleep(10)  # debug
        return False

    payload_1 = payload(sol_x_1, sol_y_1)
    payload_2 = payload(sol_x_2, sol_y_2)

    res_3 = in_session.put(url, json=payload_1, headers=headers)
    if res_3.status_code == 200:
        # print(f"[Debug] 解 1 签到成功。对应经纬度：{sol_x_1, sol_y_1}")  # debug
        # print(res_3.json())  # debug
        # time.sleep(10)  # debug
        return True
    else:
        print(res_3.json())
        res_4 = in_session.put(url, json=payload_2, headers=headers)
        if res_4.status_code == 200:
            # print(f"[Debug] 解 2 签到成功。对应经纬度：{sol_x_2, sol_y_2}")  # debug
            # print(res_4.json())  # debug
            # time.sleep(10)  # debug
            return True
    # print(res_4.json())  # debug

    # print("[Debug] 失败了。")  # debug
    # time.sleep(10)  # debug
    return False
