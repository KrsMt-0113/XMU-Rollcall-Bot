# 本脚本用于测试厦门大学统一身份认证登录 TronClass 的跳转过程
import requests, re
from login import encryptPassword, USERNAME, pwd
from urllib.parse import urlparse, parse_qs

def login():
    url = "https://c-identity.xmu.edu.cn/auth/realms/xmu/protocol/openid-connect/auth"
    url_2 = "https://c-identity.xmu.edu.cn/auth/realms/xmu/protocol/openid-connect/token"
    url_3 = "https://lnt.xmu.edu.cn/api/login?login=access_token"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36"
    }
    params = {
        "scope": "openid",
        "response_type": "code",
        "client_id": "TronClassH5",
        "redirect_uri": "https://c-mobile.xmu.edu.cn/identity-web-login-callback?_h5=true"
    }
    try:
        s = requests.Session()
        headers_1 = s.get(url, headers=headers, params=params, allow_redirects=False).headers  # 303 See Other
        location = headers_1['location']
        headers_2 = s.get(location, headers=headers, allow_redirects=False).headers  # 303 See Other
        location = headers_2['location']
        res_3 = s.get(location, headers=headers, allow_redirects=False)
        html = res_3.text
        try:
            salt = re.search(r'id="pwdEncryptSalt"\s+value="([^"]+)"', html).group(1)
            execution = re.search(r'name="execution"\s+value="([^"]+)"', html).group(1)
        except Exception as e:
            salt = None
            execution = None
            print(e)
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
        headers_4 = s.post(location, data=data, headers=headers, allow_redirects=False).headers # 302 Found
        location = headers_4['location']
        headers_5 = s.get(location, headers=headers, allow_redirects=False).headers # 302 Found
        location = headers_5['location']
        params = parse_qs(urlparse(location).query)
        code = params['code']
        data = {
            "client_id": "TronClassH5",
            "grant_type": "authorization_code",
            "code": code[0],
            "redirect_uri": "https://c-mobile.xmu.edu.cn/identity-web-login-callback?_h5=true",
            "scope": "openid"
        }
        res_6 = s.post(url_2, data=data, headers=headers).json() # 200 OK
        access_token = res_6['access_token']
        data = {
            "access_token": access_token,
            "org_id": 1
        }
        if s.post(url_3, json=data).status_code == 200:
            return s
        else:
            return None
    except Exception as e:
        print("Login failed:", e)
        return None