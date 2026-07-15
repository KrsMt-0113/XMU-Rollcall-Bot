import os
import json
import requests

base_url = "https://lnt.xmu.edu.cn"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def clear_screen():
    """清屏"""
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def save_session(sess: requests.Session, path: str):
    """保存session到文件"""
    try:
        cj_dict = requests.utils.dict_from_cookiejar(sess.cookies)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cj_dict, f)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        return True
    except Exception:
        return False

def load_session(sess: requests.Session, path: str):
    """从文件加载session"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            cj_dict = json.load(f)
        sess.cookies = requests.utils.cookiejar_from_dict(cj_dict)
        return True
    except Exception:
        return False

def verify_session(sess: requests.Session) -> dict:
    """验证session是否有效"""
    try:
        resp = sess.get(f"{base_url}/api/profile", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "name" in data:
                return data
    except Exception:
        pass
    return {}
