import requests, base64, random, re, time, json, os, sys
from Crypto.Cipher import AES
from misc import c

base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
file_path = os.path.join(base_dir, "info.txt")

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
    USERNAME = lines[0].strip()
    pwd = lines[1].strip()
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
cookies = {
    'org.springframework.web.servlet.i18n.CookieLocaleResolver.LOCALE': 'zh_CN'
}
login_url = "https://ids.xmu.edu.cn/authserver/login"
AES_CHARS = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"

def randomString(n):
    return ''.join(random.choice(AES_CHARS) for _ in range(n))

def pad(data):
    pad_len = 16 - (len(data) % 16)
    return data + chr(pad_len) * pad_len

def encryptPassword(password, salt):
    plaintext = randomString(64) + password
    key = salt.encode()
    iv = randomString(16).encode()
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(plaintext).encode())
    return base64.b64encode(encrypted).decode()

def login():
    s = requests.Session()
    res = s.post(login_url, headers=headers)
    html = res.text

    try:
        salt = re.search(r'id="pwdEncryptSalt"\s+value="([^"]+)"', html).group(1)
        execution = re.search(r'name="execution"\s+value="([^"]+)"', html).group(1)
    except Exception:
        return None

    enc = encryptPassword(pwd, salt)

    data = {
        "username": USERNAME,
        "password": enc,
        "captcha": '',
        "_eventId": "submit",
        "cllt": "userNameLogin",
        "dllt": "generalLogin",
        "lt": '',
        "execution": execution
    }
    res2 = s.post(login_url, headers=headers, data=data, cookies=cookies, allow_redirects=False)
    if res2.status_code == 302:
        c()
        personalInfo = s.get("https://ids.xmu.edu.cn/personalInfo/common/getUserConf", headers=headers).text
        name = json.loads(personalInfo)["datas"]["cn"]
        print(f"Welcome back, {name}.")
        time.sleep(3)
        return s
    else:
        c()
        print("Login failed. Check your username/password, or contact the developer for help.\nClosed in 5 seconds...")
        time.sleep(5)
        return None

# # 测试用
# import time
# if __name__ == "__main__":
#     time1 = time.time()
#     s = login()
#     time2 = time.time()
#     if s: print(s.get("https://lnt.xmu.edu.cn/api/radar/rollcalls", headers=headers).text)
#     print(f"Login time: {time2 - time1:.2f} seconds")
