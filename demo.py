import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
# chrome_options.add_argument("--start-maximized")   # 有头调试
chrome_options.add_argument("--headless")  # 无头运行
driver = webdriver.Chrome(options=chrome_options)
driver.get("填写你的登录平台URL")
driver.find_element(By.ID, "username").send_keys("填写你的账号")
driver.find_element(By.ID, "password").send_keys("填写你的密码")
driver.find_element(By.ID, "login_submit").click()

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0",
    "Content-Type": "application/json"
}

requests.get(
    "这里填写签到列表接口URL",
    cookies={c['name']: c['value'] for c in driver.get_cookies()}
)

payload = {
    # 按照demo.md中的说明填写签到所需的载荷
}

requests.put(
    f"这里填写签到接口URL",
    json=payload,  # 这里的 payload 是上面提到的载荷
    cookies={c['name']: c['value'] for c in driver.get_cookies()},
    headers = headers
)