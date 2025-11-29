import time, os, sys, requests
from xmulogin import xmulogin
from misc import c, a, t, l, v, s

base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
file_path = os.path.join(base_dir, "info.txt")
cookies = os.path.join(base_dir, "cookies.json")

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
    USERNAME = lines[0].strip()
    pwd = lines[1].strip()

interval = 1
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
session = None
rollcalls_url = f"{base_url}/api/radar/rollcalls"
c()

print("Welcome to XMU Rollcall Bot CLI!\nLogging you in...")

if os.path.exists(cookies):
    session_candidate = requests.Session()
    if l(session_candidate, cookies):
        profile = v(session_candidate)
        if profile:
            session = session_candidate

if not session:
    time.sleep(5)
    session = xmulogin(type=3, username=USERNAME, password=pwd)
    if session:
        s(session, cookies)
    else:
        print("Login failed. Please check your credentials.")
        time.sleep(5)
        exit(1)
profile = session.get(f"{base_url}/api/profile", headers=headers).json()
name = profile["name"]

temp_data = {'rollcalls': []}
query_count = 0
start_time = time.time()
while True:
    c()
    now = time.time()
    print("====== XMU Rollcall Bot CLI ======")
    print("--------- version 3.0.0 ----------\n")
    print(t(name),'\n')
    print(f"Local   time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    print(f"Running time: {int(now - start_time)} seconds\n")
    print("======= Querying rollcalls =======")
    time.sleep(interval)
    try:
        data = session.get(rollcalls_url, headers=headers).json()
        query_count += 1
        if temp_data == data:
            continue
        else:
            temp_data = data
            if len(temp_data['rollcalls']) > 0:
                temp_data = a(temp_data, session)
    except Exception as e:
        print("An error occurred:", str(e))
        exit(1)
