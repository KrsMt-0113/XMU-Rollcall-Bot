import uuid
import time
import threading
import requests
import json
from serverchan_sdk import sc_send
from concurrent.futures import ThreadPoolExecutor, as_completed

with open("config.json") as f:
    config = json.load(f)
    sendkey = config["sendkey"]

def pad(i):
    return str(i).zfill(4)

def send_code(driver, rollcall_id):
    stop_flag = threading.Event()
    url = f"https://lnt.xmu.edu.cn/api/rollcall/{rollcall_id}/answer_number_rollcall"

    def put_request(i, headers, cookies):
        if stop_flag.is_set():
            return None
        payload = {
            "deviceId": str(uuid.uuid1()),
            "numberCode": pad(i)
        }
        try:
            r = requests.put(url, json=payload, headers=headers, cookies=cookies, timeout=5)
            if r.status_code == 200:
                stop_flag.set()
                return pad(i)
        except Exception as e:
            pass
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0",
        "Content-Type": "application/json"
    }
    cookies_list = driver.get_cookies()
    cookies = {c['name']: c['value'] for c in cookies_list}
    print("正在遍历签到码...")
    # sc_send(sendkey, "签到机器人", "签到码遍历中...", {"tags": "签到机器人"})
    t00 = time.time()
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(put_request, i, headers, cookies) for i in range(10000)]
        for f in as_completed(futures):
            res = f.result()
            if res is not None:
                print("签到码:", res)
                t01 = time.time()
                print("用时: %.2f 秒" % (t01 - t00))
                sc_send(sendkey, "签到机器人", f"签到码: {res} ,签到成功! 耗时 %.2f 秒。"%(t01 - t00), {"tags": "签到机器人"})
                return True
    t01 = time.time()
    print("失败。\n用时: %.2f 秒" % (t01 - t00))
    # sc_send(sendkey, "签到机器人", f"签到失败，请手动签到。", {"tags": "签到机器人"})
    return False
