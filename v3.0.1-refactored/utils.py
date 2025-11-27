"""
Utility functions for XMU Rollcall Bot
Provides common helpers for console output, session management, etc.
"""

import os
import json
import time
import shutil
import re
import requests
from config import BASE_URL, HEADERS, Colors


def clear_console():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_greeting(name: str) -> str:
    """
    Get time-based greeting message
    
    Args:
        name: User's name
        
    Returns:
        Greeting string like "Good morning, {name}!"
    """
    hour = time.localtime().tm_hour
    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    return f"{greeting}, {name}!"


def format_time(seconds: int) -> str:
    """
    Format seconds into human-readable time string
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted string like "1h 23m 45s"
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def get_terminal_width() -> int:
    """Get terminal width, default to 80"""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80


_ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text: str) -> str:
    """Remove ANSI color codes from text"""
    return _ANSI_ESCAPE.sub('', text)


def center_text(text: str, width: int = None) -> str:
    """
    Center text with ANSI color support
    
    Args:
        text: Text to center (can contain ANSI codes)
        width: Terminal width (auto-detect if None)
        
    Returns:
        Centered text string
    """
    if width is None:
        width = get_terminal_width()
    text_len = len(strip_ansi(text))
    if text_len >= width:
        return text
    left_padding = (width - text_len) // 2
    return ' ' * left_padding + text


def save_session(session: requests.Session, path: str) -> bool:
    """
    Save session cookies to file
    
    Args:
        session: Requests session object
        path: File path to save cookies
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        cookie_dict = requests.utils.dict_from_cookiejar(session.cookies)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cookie_dict, f)
        return True
    except Exception as e:
        print(f"{Colors.WARNING}Failed to save session: {e}{Colors.ENDC}")
        return False


def load_session(session: requests.Session, path: str) -> bool:
    """
    Load session cookies from file
    
    Args:
        session: Requests session object to load into
        path: File path to load cookies from
        
    Returns:
        True if loaded successfully, False otherwise
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            cookie_dict = json.load(f)
        session.cookies = requests.utils.cookiejar_from_dict(cookie_dict)
        return True
    except Exception as e:
        return False


def verify_session(session: requests.Session) -> dict:
    """
    Verify if session is still valid by fetching profile
    
    Args:
        session: Requests session to verify
        
    Returns:
        User profile dict if valid, empty dict otherwise
    """
    try:
        resp = session.get(f"{BASE_URL}/api/profile", headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "name" in data:
                return data
    except Exception:
        pass
    return {}


def print_separator(char: str = "-", color: str = Colors.GRAY):
    """Print a full-width separator line"""
    width = get_terminal_width()
    print(f"{color}{char * width}{Colors.ENDC}")
