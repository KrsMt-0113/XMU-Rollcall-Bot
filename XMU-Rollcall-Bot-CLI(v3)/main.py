import time, asyncio
# from login import login
from tst_login import login
from misc import c, a, t

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

rollcalls_url = f"{base_url}/api/radar/rollcalls"
c()

async def main_loop():
    print("Welcome to XMU Rollcall Bot CLI!\nLogging you in...")
    session = await login()
    if not session:
        exit(1)
    
    async with session:
        async with session.get(f"{base_url}/api/profile", headers=headers) as response:
            profile = await response.json()
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
            await asyncio.sleep(interval)
            try:
                async with session.get(rollcalls_url, headers=headers) as response:
                    data = await response.json()
                query_count += 1
                if temp_data == data:
                    continue
                else:
                    temp_data = data
                    if len(temp_data['rollcalls']) > 0:
                        temp_data = await a(temp_data, session)
            except Exception as e:
                print("An error occurred:", str(e))
                exit(1)

if __name__ == "__main__":
    asyncio.run(main_loop())
