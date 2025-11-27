"""
Rollcall handling module
Manages rollcall detection, parsing and response logic
"""

import time
import requests
from typing import List, Dict, Optional
from config import Colors
from verify import submit_number_code, submit_radar_rollcall


class Rollcall:
    """Represents a single rollcall activity"""
    
    def __init__(self, data: dict):
        self.course_title = data.get('course_title', '')
        self.created_by_name = data.get('created_by_name', '')
        self.department_name = data.get('department_name', '')
        self.is_expired = data.get('is_expired', False)
        self.is_number = data.get('is_number', False)
        self.is_radar = data.get('is_radar', False)
        self.rollcall_id = data.get('rollcall_id', '')
        self.rollcall_status = data.get('rollcall_status', '')
        self.scored = data.get('scored', False)
        self.status = data.get('status', '')
    
    def get_type_description(self) -> str:
        """Get human-readable rollcall type"""
        if self.is_radar:
            return "Radar rollcall"
        elif self.is_number:
            return "Number rollcall"
        else:
            return "QRcode rollcall"
    
    def should_answer(self) -> bool:
        """Check if this rollcall needs to be answered"""
        return self.status == 'absent' and not self.is_expired
    
    def is_already_answered(self) -> bool:
        """Check if already answered"""
        return self.status == 'on_call_fine'


class RollcallHandler:
    """Handles rollcall detection and response"""
    
    def __init__(self, session: requests.Session):
        self.session = session
    
    def parse_rollcalls(self, data: dict) -> List[Rollcall]:
        """
        Parse rollcall data from API response
        
        Args:
            data: API response containing rollcalls
            
        Returns:
            List of Rollcall objects
        """
        rollcalls_data = data.get('rollcalls', [])
        return [Rollcall(rc) for rc in rollcalls_data]
    
    def handle_rollcall(self, rollcall: Rollcall, index: int, total: int) -> bool:
        """
        Handle a single rollcall activity
        
        Args:
            rollcall: Rollcall object to handle
            index: Current rollcall index (0-based)
            total: Total number of rollcalls
            
        Returns:
            True if handled successfully, False otherwise
        """
        print(f"\n{Colors.BOLD}Rollcall {index + 1} of {total}:{Colors.ENDC}")
        print(f"Course: {Colors.OKCYAN}{rollcall.course_title}{Colors.ENDC}")
        print(f"Created by: {rollcall.department_name} {rollcall.created_by_name}")
        print(f"Type: {Colors.WARNING}{rollcall.get_type_description()}{Colors.ENDC}")
        
        # Already answered
        if rollcall.is_already_answered():
            print(f"{Colors.OKGREEN}Already answered.{Colors.ENDC}")
            return True
        
        # Not absent, no need to answer
        if not rollcall.should_answer():
            print(f"{Colors.GRAY}No need to answer (status: {rollcall.status}){Colors.ENDC}")
            return True
        
        # Handle different rollcall types
        try:
            if rollcall.is_number and not rollcall.is_radar:
                # Number code rollcall
                return submit_number_code(self.session, rollcall.rollcall_id)
            elif rollcall.is_radar:
                # Radar rollcall
                return submit_radar_rollcall(self.session, rollcall.rollcall_id)
            else:
                # QR code rollcall (not yet implemented)
                print(f"{Colors.WARNING}QR code rollcall not supported yet.{Colors.ENDC}")
                return False
        except Exception as e:
            print(f"{Colors.FAIL}Error handling rollcall: {e}{Colors.ENDC}")
            return False
    
    def process_rollcalls(self, data: dict) -> bool:
        """
        Process all rollcalls in the data
        
        Args:
            data: API response containing rollcalls
            
        Returns:
            True if all rollcalls processed successfully
        """
        rollcalls = self.parse_rollcalls(data)
        
        if not rollcalls:
            return True
        
        print(f"\n{Colors.WARNING}{Colors.BOLD}{'!' * 50}{Colors.ENDC}")
        print(f"{Colors.WARNING}{Colors.BOLD}NEW ROLLCALL DETECTED{Colors.ENDC}")
        print(f"{Colors.WARNING}{Colors.BOLD}{'!' * 50}{Colors.ENDC}")
        print(f"{time.strftime('%H:%M:%S', time.localtime())} - Found {len(rollcalls)} rollcall(s)\n")
        
        success_count = 0
        for i, rollcall in enumerate(rollcalls):
            if self.handle_rollcall(rollcall, i, len(rollcalls)):
                success_count += 1
        
        print(f"\n{Colors.BOLD}Summary:{Colors.ENDC} {success_count}/{len(rollcalls)} handled successfully")
        
        return success_count == len(rollcalls)
