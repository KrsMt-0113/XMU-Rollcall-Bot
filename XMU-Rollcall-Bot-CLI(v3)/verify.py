import uuid, requests, time, asyncio, aiohttp, os, sys

base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
file_path = os.path.join(base_dir, "info.txt")

base_url = "https://lnt.xmu.edu.cn"

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0",
    "Content-Type": "application/json"
}

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

    async def put_request(i, session, stop_flag, url, headers, sem, timeout):
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
                async with session.put(url, json=payload, timeout=timeout) as r:
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
        async with aiohttp.ClientSession(headers=headers, cookies=in_session.cookies) as session:
            tasks = [asyncio.create_task(put_request(i, session, stop_flag, url, headers, sem, timeout)) for i in range(10000)]
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
    res = requests.put(url, json=payload, headers=headers, cookies=in_session.cookies)
    if res.status_code == 200:
        print("Radar rollcall answered successfully.")
        return True
    return False