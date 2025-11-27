"""
XMU Rollcall Bot - Main Entry Point
Automated rollcall monitoring and response system for XMU Digital Teaching Platform

Author: KrsMt
Version: 3.0.1 Refactored
"""

import time
import os
import sys
import requests
from xmulogin import xmulogin

from config import BASE_URL, ROLLCALLS_URL, HEADERS, POLL_INTERVAL, Colors
from utils import (
    clear_console, 
    save_session, 
    load_session, 
    verify_session,
    print_separator
)
from rollcall import RollcallHandler
from display import (
    print_banner, 
    print_login_status, 
    LiveDashboard,
    print_exit_message
)


class RollcallBot:
    """Main rollcall bot application"""
    
    def __init__(self, config_path: str = "info.txt", cookies_path: str = "cookies.json"):
        """
        Initialize rollcall bot
        
        Args:
            config_path: Path to configuration file
            cookies_path: Path to cookies storage file
        """
        self.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.config_path = os.path.join(self.base_dir, config_path)
        self.cookies_path = os.path.join(self.base_dir, cookies_path)
        
        self.session = None
        self.username = None
        self.password = None
        self.user_profile = None
        
    def load_config(self) -> bool:
        """
        Load configuration from file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                self.username = lines[0].strip()
                self.password = lines[1].strip()
            return True
        except Exception as e:
            print(f"{Colors.FAIL}Error loading config: {e}{Colors.ENDC}")
            return False
    
    def try_restore_session(self) -> bool:
        """
        Try to restore session from saved cookies
        
        Returns:
            True if session restored successfully, False otherwise
        """
        if not os.path.exists(self.cookies_path):
            return False
        
        print(f"{Colors.OKCYAN}[Step 2/3]{Colors.ENDC} Found cached session, attempting to restore...")
        
        session_candidate = requests.Session()
        if load_session(session_candidate, self.cookies_path):
            profile = verify_session(session_candidate)
            if profile:
                self.session = session_candidate
                self.user_profile = profile
                print_login_status("Session restored successfully", True)
                return True
            else:
                print_login_status("Session expired, will re-login", False)
        else:
            print_login_status("Failed to load session", False)
        
        return False
    
    def login(self) -> bool:
        """
        Login to XMU system
        
        Returns:
            True if login successful, False otherwise
        """
        print(f"{Colors.OKCYAN}[Step 2/3]{Colors.ENDC} Logging in with credentials...")
        time.sleep(2)
        
        try:
            self.session = xmulogin(type=3, username=self.username, password=self.password)
            if self.session:
                save_session(self.session, self.cookies_path)
                print_login_status("Login successful", True)
                return True
            else:
                print_login_status("Login failed. Please check your credentials", False)
                return False
        except Exception as e:
            print_login_status(f"Login error: {e}", False)
            return False
    
    def fetch_profile(self) -> bool:
        """
        Fetch user profile information
        
        Returns:
            True if successful, False otherwise
        """
        print(f"{Colors.OKCYAN}[Step 3/3]{Colors.ENDC} Fetching user profile...")
        
        try:
            response = self.session.get(f"{BASE_URL}/api/profile", headers=HEADERS, timeout=10)
            if response.status_code == 200:
                self.user_profile = response.json()
                print_login_status(f"Welcome, {self.user_profile['name']}", True)
                return True
            else:
                print_login_status("Failed to fetch profile", False)
                return False
        except Exception as e:
            print_login_status(f"Profile fetch error: {e}", False)
            return False
    
    def initialize(self) -> bool:
        """
        Initialize bot: load config, login, and prepare session
        
        Returns:
            True if initialization successful, False otherwise
        """
        clear_console()
        print_banner()
        print(f"\n{Colors.BOLD}Initializing XMU Rollcall Bot...{Colors.ENDC}\n")
        print_separator()
        
        # Step 1: Load configuration
        print(f"\n{Colors.OKCYAN}[Step 1/3]{Colors.ENDC} Checking credentials...")
        if not self.load_config():
            return False
        
        # Step 2: Try restore or login
        if not self.try_restore_session():
            if not self.login():
                time.sleep(5)
                return False
        
        # Step 3: Fetch profile if not already done
        if not self.user_profile:
            if not self.fetch_profile():
                return False
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}Initialization complete!{Colors.ENDC}")
        print(f"\n{Colors.GRAY}Starting monitor in 3 seconds...{Colors.ENDC}")
        time.sleep(3)
        
        return True
    
    def run(self):
        """Main monitoring loop"""
        if not self.initialize():
            print(f"\n{Colors.FAIL}Initialization failed. Exiting...{Colors.ENDC}")
            return
        
        handler = RollcallHandler(self.session)
        dashboard = LiveDashboard(self.user_profile['name'], time.time())
        
        query_count = 0
        last_data = {'rollcalls': []}
        last_query_time = 0
        
        # Initialize dashboard
        dashboard.initialize(query_count)
        
        try:
            while True:
                current_time = time.time()
                elapsed = int(current_time - dashboard.start_time)
                
                # Query API every POLL_INTERVAL seconds
                if elapsed > last_query_time:
                    last_query_time = elapsed
                    
                    try:
                        response = self.session.get(ROLLCALLS_URL, headers=HEADERS, timeout=10)
                        if response.status_code != 200:
                            raise Exception(f"API returned status {response.status_code}")
                        
                        data = response.json()
                        query_count += 1
                        
                        # Update dashboard
                        dashboard.update_status(query_count)
                        
                        # Check for new rollcalls
                        if data != last_data:
                            last_data = data
                            if len(data.get('rollcalls', [])) > 0:
                                # New rollcall detected - handle it
                                clear_console()
                                handler.process_rollcalls(data)
                                
                                print_separator("=")
                                print(f"\n{Colors.GRAY}Press Ctrl+C to exit, continuing monitor...{Colors.ENDC}\n")
                                
                                try:
                                    time.sleep(3)
                                except KeyboardInterrupt:
                                    raise
                                
                                # Refresh dashboard
                                clear_console()
                                dashboard.initialized = False
                                dashboard.initialize(query_count)
                    
                    except KeyboardInterrupt:
                        raise
                    except Exception as e:
                        clear_console()
                        print(f"\n{Colors.FAIL}{Colors.BOLD}Error occurred:{Colors.ENDC} {str(e)}")
                        print(f"{Colors.GRAY}Exiting...{Colors.ENDC}\n")
                        sys.exit(1)
                
                # Sleep briefly to avoid busy loop
                try:
                    time.sleep(0.1)
                except KeyboardInterrupt:
                    raise
        
        except KeyboardInterrupt:
            clear_console()
            print_exit_message(query_count, dashboard.start_time)
            sys.exit(0)


def main():
    """Entry point"""
    bot = RollcallBot()
    bot.run()


if __name__ == "__main__":
    main()
