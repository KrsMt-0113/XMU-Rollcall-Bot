"""
Display module for terminal UI
Handles all console output formatting and display logic
"""

import time
import re
from config import Colors
from utils import get_terminal_width, center_text, strip_ansi, print_separator, get_greeting, format_time


def print_banner():
    """Print application banner"""
    width = get_terminal_width()
    line = '=' * width
    
    title1 = "XMU Rollcall Bot CLI"
    title2 = "Version 3.0.1 Refactored"
    
    print(f"{Colors.OKCYAN}{line}{Colors.ENDC}")
    print(center_text(f"{Colors.BOLD}{title1}{Colors.ENDC}"))
    print(center_text(f"{Colors.GRAY}{title2}{Colors.ENDC}"))
    print(f"{Colors.OKCYAN}{line}{Colors.ENDC}")


_COLOR_PALETTE = (
    Colors.FAIL,      # Red
    Colors.WARNING,   # Yellow
    Colors.OKGREEN,   # Green
    Colors.OKCYAN,    # Cyan
    Colors.OKBLUE,    # Blue
    Colors.HEADER     # Purple
)


def get_rainbow_text(text: str, offset: int = 0) -> str:
    """
    Apply rainbow colors to each character
    
    Args:
        text: Text to colorize
        offset: Color offset for animation
        
    Returns:
        Colored text string
    """
    color_count = len(_COLOR_PALETTE)
    return ''.join(
        _COLOR_PALETTE[(i + offset) % color_count] + char
        for i, char in enumerate(text)
    ) + Colors.ENDC


def print_footer(offset: int = 0):
    """
    Print footer with rainbow effect
    
    Args:
        offset: Color offset for animation
    """
    text = "XMU-Rollcall-Bot @ KrsMt"
    colored = get_rainbow_text(text, offset)
    print(center_text(colored))


def print_login_status(message: str, is_success: bool = True):
    """
    Print login status message
    
    Args:
        message: Status message
        is_success: True for success, False for failure
    """
    if is_success:
        print(f"{Colors.OKGREEN}[SUCCESS]{Colors.ENDC} {message}")
    else:
        print(f"{Colors.FAIL}[FAILED]{Colors.ENDC} {message}")


def print_dashboard(name: str, start_time: float, query_count: int):
    """
    Print main dashboard UI
    
    Args:
        name: User's name
        start_time: Unix timestamp when monitoring started
        query_count: Number of queries performed
    """
    print_banner()
    
    # Get current time and greeting
    local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    greeting = get_greeting(name)
    
    # Calculate running time
    running_time = int(time.time() - start_time)
    
    # User greeting
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}{greeting}{Colors.ENDC}\n")
    
    # System status
    print(f"{Colors.BOLD}SYSTEM STATUS{Colors.ENDC}")
    print_separator()
    print(f"{Colors.BOLD}Current Time:{Colors.ENDC}    {Colors.OKCYAN}{local_time}{Colors.ENDC}")
    print(f"{Colors.BOLD}Running Time:{Colors.ENDC}    {Colors.OKGREEN}{format_time(running_time)}{Colors.ENDC}")
    print(f"{Colors.BOLD}Query Count:{Colors.ENDC}     {Colors.WARNING}{query_count}{Colors.ENDC}")
    
    # Monitoring status
    print(f"\n{Colors.BOLD}ROLLCALL MONITOR{Colors.ENDC}")
    print_separator()
    print(f"{Colors.OKGREEN}Status:{Colors.ENDC} Active - Monitoring for new rollcalls...")
    print(f"{Colors.GRAY}Press Ctrl+C to exit{Colors.ENDC}\n")
    print_separator()


class LiveDashboard:
    """
    Live updating dashboard without full screen refresh
    Optimized for minimal flickering
    """
    
    # Line positions in terminal (1-indexed)
    TIME_LINE = 10
    RUNTIME_LINE = 11
    QUERY_LINE = 12
    
    def __init__(self, name: str, start_time: float):
        self.name = name
        self.start_time = start_time
        self.initialized = False
    
    def initialize(self, query_count: int):
        """Initialize dashboard with full print"""
        print_dashboard(self.name, self.start_time, query_count)
        self.initialized = True
    
    def _update_line(self, line_num: int, label: str, value: str, color: str):
        """
        Update a single line in terminal without clearing screen
        
        Args:
            line_num: Line number (1-indexed from top)
            label: Label text
            value: Value text
            color: ANSI color code
        """
        # Hide cursor, save position
        print("\033[?25l\033[s", end='')
        
        # Move to line, clear it, print new content
        print(f"\033[{line_num};0H\033[2K", end='')
        print(f"{Colors.BOLD}{label}{Colors.ENDC}    {color}{value}{Colors.ENDC}", end='')
        
        # Restore cursor position and show cursor
        print("\033[u\033[?25h", end='', flush=True)
    
    def update_status(self, query_count: int):
        """
        Update status lines without full refresh
        
        Args:
            query_count: Current query count
        """
        if not self.initialized:
            self.initialize(query_count)
            return
        
        local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        running_time = format_time(int(time.time() - self.start_time))
        
        self._update_line(self.TIME_LINE, "Current Time:", local_time, Colors.OKCYAN)
        self._update_line(self.RUNTIME_LINE, "Running Time:", running_time, Colors.OKGREEN)
        self._update_line(self.QUERY_LINE, "Query Count: ", str(query_count), Colors.WARNING)


def print_exit_message(query_count: int, start_time: float):
    """
    Print graceful exit message
    
    Args:
        query_count: Total queries performed
        start_time: Start timestamp
    """
    total_time = format_time(int(time.time() - start_time))
    
    print(f"\n{center_text(f'{Colors.WARNING}Shutting down gracefully...{Colors.ENDC}')}")
    print(f"{center_text(f'{Colors.GRAY}Total queries performed: {query_count}{Colors.ENDC}')}")
    print(f"{center_text(f'{Colors.GRAY}Total running time: {total_time}{Colors.ENDC}')}")
    print(f"\n{center_text(f'{Colors.OKGREEN}Goodbye!{Colors.ENDC}')}\n")
