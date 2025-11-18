# 本脚本用于测试厦门大学统一身份认证登录 TronClass 的跳转过程
import aiohttp, re
from login import encryptPassword, USERNAME, pwd
from urllib.parse import urlparse, parse_qs

async def login():
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
        # Create session outside the context manager to return it
        session = aiohttp.ClientSession()
        try:
            # First request: GET with params, don't follow redirects
            async with session.get(url, headers=headers, params=params, allow_redirects=False) as response:
                location = response.headers['location']
            
            # Second request: GET to location, don't follow redirects
            async with session.get(location, headers=headers, allow_redirects=False) as response:
                location = response.headers['location']
            
            # Third request: GET to location, get HTML content
            async with session.get(location, headers=headers, allow_redirects=False) as response:
                html = await response.text()
            
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
            
            # Fourth request: POST login data, don't follow redirects
            async with session.post(location, data=data, headers=headers, allow_redirects=False) as response:
                location = response.headers['location']
            
            # Fifth request: GET to location, don't follow redirects
            async with session.get(location, headers=headers, allow_redirects=False) as response:
                location = response.headers['location']
            
            params = parse_qs(urlparse(location).query)
            code = params['code']
            data = {
                "client_id": "TronClassH5",
                "grant_type": "authorization_code",
                "code": code[0],
                "redirect_uri": "https://c-mobile.xmu.edu.cn/identity-web-login-callback?_h5=true",
                "scope": "openid"
            }
            
            # Sixth request: POST to get access token
            async with session.post(url_2, data=data, headers=headers) as response:
                res_6 = await response.json()
            
            access_token = res_6['access_token']
            data = {
                "access_token": access_token,
                "org_id": 1
            }
            
            # Final request: POST to login with access token
            async with session.post(url_3, json=data) as response:
                if response.status == 200:
                    # Return session with cookies from the login process
                    # Caller is responsible for closing the session
                    return session
                else:
                    await session.close()
                    return None
        except Exception as e:
            # Close session on error
            await session.close()
            raise
    except Exception as e:
        print("Login failed:", e)
        return None