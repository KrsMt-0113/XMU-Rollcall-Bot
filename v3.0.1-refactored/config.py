"""
Configuration module for XMU Rollcall Bot
Handles all configuration constants and settings
"""

# API URLs
BASE_URL = "https://lnt.xmu.edu.cn"
LOGIN_URL = "https://ids.xmu.edu.cn/authserver/login"
ROLLCALLS_URL = f"{BASE_URL}/api/radar/rollcalls"
PROFILE_URL = f"{BASE_URL}/api/profile"

# HTTP Headers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://ids.xmu.edu.cn/authserver/login",
}

# Polling settings
POLL_INTERVAL = 1  # seconds

# ANSI Color codes
class Colors:
    """Terminal color codes"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GRAY = '\033[90m'
    WHITE = '\033[97m'

# Async request settings
MAX_CONCURRENT_REQUESTS = 200
REQUEST_TIMEOUT = 5
