# 厦大数字化教学平台自动签到机器人 V1.0
# by KrsMt-0113
import time
import json
import uuid
import requests
from serverchan_sdk import sc_send
from tkinter import Tk, Label
from PIL import ImageTk, Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from parse_rollcalls import parse_rollcalls

# 读取学号、密码、Server酱sendkey
with open("config.json") as f:
    config = json.load(f)
    username = config["username"]
    password = config["password"]
    sendkey = config["sendkey"]

# 签到列表获取接口，轮询间隔，轮询脚本
api_url = "https://lnt.xmu.edu.cn/api/radar/rollcalls"
interval = 1.5
fetch_script = """
const url = arguments[0];
const callback = arguments[arguments.length - 1];
fetch(url, {credentials: 'include'})
  .then(resp => resp.text().then(text => callback({status: resp.status, ok: resp.ok, text: text})))
  .catch(err => callback({error: String(err)}));
"""

chrome_options = Options()
# chrome_options.add_argument("--start-maximized")   # 有头调试
chrome_options.add_argument("--headless")  # 无头运行

# 启动selenium
print("正在初始化...")
sc_send(sendkey, "签到机器人", "正在初始化...", {"tags": "签到机器人"})
driver = webdriver.Chrome(options=chrome_options)

# 访问登录页面,不开VPN好像连不上
driver.get("https://lnt.xmu.edu.cn")
print("已连接到厦大数字化教学平台。")

# 检查是否需要验证码，有验证码直接登录，否则扫码
# 待优化: 提取验证码图片，OCR识别或用户自行登录
ts = int(time.time() * 1000)
temp_header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"}
temp_url = f"https://ids.xmu.edu.cn/authserver/checkNeedCaptcha.htl?username={username}&_={ts}"
res_data = requests.get(temp_url,cookies={c['name']: c['value'] for c in driver.get_cookies()},headers=temp_header).json()
if res_data['isNeed'] == False:
    print("登录无需验证,正在登录...")
    sc_send(sendkey, "签到机器人", "账号密码登录中...", {"tags": "签到机器人"})
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "userNameLogin_a"))
    ).click()
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "login_submit").click()
    time.sleep(1)
else:
    print("账号密码登录暂时不可用，请用企业微信扫码登录。")
    sc_send(sendkey, "签到机器人", "需要图形验证码，请扫码登录。", {"tags": "签到机器人"})
    driver.find_element(By.ID, "qrLogin_a").click()
    driver.set_window_size(1920, 1080)
    time.sleep(1)
    driver.get_screenshot_as_file("cache/fullpage.png")
    root = Tk()
    img = Image.open("cache/fullpage.png")
    tk_img = ImageTk.PhotoImage(img)
    Label(root, image=tk_img).pack()
    root.mainloop()

res = requests.get(api_url, cookies={c['name']: c['value'] for c in driver.get_cookies()})
if res.status_code == 200:
    print("登录成功！五秒后进入监控...")
    sc_send(sendkey, "签到机器人", "登录成功！五秒后进入监控模式...", {"tags": "签到机器人"})
else:
    print("登录失败。")
    driver.quit()
    time.sleep(5)
    exit(0)

time.sleep(5)


deviceID = uuid.uuid4()
print(f"签到监控启动。")
sc_send(sendkey, "签到机器人", "签到监控已启动。", {"tags": "签到机器人"})
start = time.time()
temp_data = {'rollcalls': []}
while True:
    res = driver.execute_async_script(fetch_script, api_url)
    if res['status'] == 200:
        text = res.get('text', '')
        try:
            data = json.loads(text)
            if temp_data == data:
                continue
            else:
                temp_data = data
                if len(temp_data['rollcalls']) > 0:
                    if not parse_rollcalls(temp_data, driver):
                        temp_data = {'rollcalls': []}
        except Exception as e:
            print(time.strftime("%H:%M:%S", time.localtime()), ":发生错误")

    elif res['status'] != 200:
        print("失去连接，请重新登录。")
        sc_send(sendkey, "签到机器人", "失去连接，监控已终止。", {"tags": "签到机器人"})
        break
    time.sleep(interval)

driver.quit()
