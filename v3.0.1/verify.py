import uuid, time, asyncio, aiohttp, os, sys
from aiohttp import CookieJar

base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
file_path = os.path.join(base_dir, "info.txt")

base_url = "https://lnt.xmu.edu.cn"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
    LATITUDE = lines[2].strip()
    LONGITUDE = lines[3].strip()

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

def send_radar(in_session, rollcall_id):
    url = f"{base_url}/api/rollcall/{rollcall_id}/answer?api_version=1.76"
    payload = {
        "accuracy": 35,
        "altitude": 0,
        "altitudeAccuracy": None,
        "deviceId": str(uuid.uuid4()),
        "heading": None,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "speed": None
    }
    res = in_session.put(url, json=payload)
    if res.status_code == 200:
        print("Radar rollcall answered successfully.")
        return True
    return False