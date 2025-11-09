### 如果你想做一个最小可用程序，那么这是你要看的...

#### 1. 登录

在我的项目中，我采用 `Selenium` 来实现自动化登录。以下是一个简单的登录示例：

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
# chrome_options.add_argument("--start-maximized")   # 有头调试
chrome_options.add_argument("--headless")  # 无头运行
driver = webdriver.Chrome(options=chrome_options)
driver.get("填写你的登录平台URL")
driver.find_element(By.ID, "username").send_keys("填写你的账号")
driver.find_element(By.ID, "password").send_keys("填写你的密码")
driver.find_element(By.ID, "login_submit").click()
```

至此，完成登录。

需要注意，此处元素的名称(`username`,`password`,`login_submit`)需要根据实际网页进行调整。

完成登录后，可以通过 `driver.get_cookies()` 获取登录后的 cookies 信息。

#### 2. 请求签到列表

获取 `cookies` 后，可以使用 `requests` 库来请求签到列表：

```python
requests.get(
    "这里填写签到列表接口URL",
    cookies={c['name']: c['value'] for c in driver.get_cookies()}
)
```

如果有签到，你会得到一份 `json` 响应，其中包括当前的签到事件，找到 `rollcall_id` 并记下来。

#### 3. 签到

获取到 `rollcall_id` 后，可以在 `api/rollcall/{rollcall_id}/answer`接口发起签到。

此时，向该接口发起 `PUT` 请求并携带相应的*载荷*即可。

对于数字签到，载荷如下：

```python
{
  "deviceId": "设备标识符，可以用 uuid.uuid4() 生成随机的设备标识符",
  "numberCode": "签到码"
}
```

对于雷达签到，载荷如下：

```python
{
  "accuracy": 35,
  "altitude": 0,
  "altitudeAccuracy": None,
  "deviceId": "设备标识符，同上",
  "heading": None,
  "latitude": "此处填写纬度",
  "longitude": "此处填写经度",
  "speed": None
}
```

设定好载荷后，发起请求：

```python
requests.put(
    f"这里填写签到接口URL",
    json=payload,  # 这里的 payload 是上面提到的载荷
    cookies={c['name']: c['value'] for c in driver.get_cookies()},
    headers = headers
)
```

这里, `headers` 用于冒充真实浏览器环境，可以写:

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0",
    "Content-Type": "application/json"
}
```

#### 4. 数字签到爆破

需要用到多线程。这个可以询问 AI 助手来帮你生成代码。例如：

```python
import threading
def attempt_sign_in(code):
    payload = {
        "deviceId": "设备标识符",
        "numberCode": code
    }
    response = requests.put(
        f"这里填写签到接口URL",
        json=payload,
        cookies={c['name']: c['value'] for c in driver.get_cookies()},
        headers=headers
    )
    if response.status_code == 200:
        print(f"签到成功，签到码为: {code}")
        return True
    return False
threads = []
for code in range(10000):  # 假设签到码是 0000 到 9999
    t = threading.Thread(target=attempt_sign_in, args=(str(code).zfill(4),))
    threads.append(t)
    t.start()
for t in threads:
    t.join()
```

## 恭喜你！你已经制作了一个最简单的自动签到机器人。