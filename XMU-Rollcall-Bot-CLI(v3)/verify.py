import uuid, time, asyncio, aiohttp, os, sys

base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
file_path = os.path.join(base_dir, "info.txt")

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
base_url = "https://lnt.xmu.edu.cn"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
    latitude = lines[2].strip()
    longitude = lines[3].strip()

def pad(i):
    return str(i).zfill(4)

async def send_code_async(session, rollcall_id):
    cookies = {cookie.name: cookie.value for cookie in session.cookies}
    url = f"{base_url}/api/rollcall/{rollcall_id}/answer_number_rollcall"
    found_code = None
    stop_flag = asyncio.Event()

    async def put_request(session, i):
        nonlocal found_code
        if stop_flag.is_set():
            return None

        payload = {
            "deviceId": str(uuid.uuid4()),
            "numberCode": pad(i)
        }
        try:
            async with session.put(url, data=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    stop_flag.set()
                    found_code = pad(i)
                    return pad(i)
        except asyncio.CancelledError:
            raise
        except Exception:
            return None
        return None

    t00 = time.time()

    connector = aiohttp.TCPConnector(limit=200)
    async with aiohttp.ClientSession(headers=headers, cookies=cookies, connector=connector) as client_session:
        tasks = [asyncio.create_task(put_request(client_session, i)) for i in range(10000)]
        pending = set(tasks)
        try:
            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                for d in done:
                    try:
                        res = d.result()
                    except Exception:
                        res = None
                    if res:
                        for p in pending:
                            p.cancel()
                        await asyncio.gather(*pending, return_exceptions=True)
                        t01 = time.time()
                        print(f"Code {res} found in {t01 - t00:.2f} seconds.")
                        return True
            t01 = time.time()
            print("Failed. \nDuration: %.2f s" % (t01 - t00))
            return False
        finally:
            for p in pending:
                p.cancel()
                await asyncio.gather(*pending, return_exceptions=True)

def send_code(session, rollcall_id):
    return asyncio.run(send_code_async(session, rollcall_id))

def send_radar(session, rollcall_id):
    url = f"{base_url}/api/rollcall/{rollcall_id}/answer?api_version=1.76"
    payload = {
        "accuracy": 35,  # 精度，写无限大会不会在哪都能签？
        "altitude": 0,
        "altitudeAccuracy": None,
        "deviceId": str(uuid.uuid4()),
        "heading": None,
        "latitude": latitude,
        "longitude": longitude,
        "speed": None
    }
    res = session.put(url, data=payload, headers=headers)
    if res.status_code == 200:
        print("Radar rollcall answered successfully!")
        return True
    return False
