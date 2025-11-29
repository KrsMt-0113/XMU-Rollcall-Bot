# "I love vibe coding." - KrsMt

import time, os, sys, requests, shutil
from xmulogin import xmulogin
from misc import c, a, l, v, s

base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
file_path = os.path.join(base_dir, "info.txt")
cookies = os.path.join(base_dir, "cookies.json")

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
    USERNAME = lines[0].strip()
    pwd = lines[1].strip()

interval = 1
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
base_url = "https://lnt.xmu.edu.cn"
session = None
rollcalls_url = f"{base_url}/api/radar/rollcalls"

# ANSI Color codes - 使用 __slots__ 减少内存占用
class Colors:
    __slots__ = ()
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
    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'
    BG_CYAN = '\033[46m'

# 预编译常用的颜色组合，避免重复拼接
BOLD_LABEL = f"{Colors.BOLD}"
CYAN_TEXT = f"{Colors.OKCYAN}"
GREEN_TEXT = f"{Colors.OKGREEN}"
YELLOW_TEXT = f"{Colors.WARNING}"
END = Colors.ENDC

def get_terminal_width():
    """获取终端宽度"""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80  # 默认宽度

# 预编译正则表达式，避免每次调用时重新编译
import re
_ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text):
    """移除ANSI颜色代码以计算实际文本长度"""
    return _ANSI_ESCAPE.sub('', text)

def center_text(text, width=None):
    """居中文本"""
    if width is None:
        width = get_terminal_width()
    text_len = len(strip_ansi(text))
    if text_len >= width:
        return text
    left_padding = (width - text_len) // 2
    return ' ' * left_padding + text

def print_banner():
    """打印美化的横幅"""
    width = get_terminal_width()
    line = '=' * width

    title1 = "XMU Rollcall Bot CLI"
    title2 = "Version 3.1.0"

    print(f"{Colors.OKCYAN}{line}{Colors.ENDC}")
    print(center_text(f"{Colors.BOLD}{title1}{Colors.ENDC}"))
    print(center_text(f"{Colors.GRAY}{title2}{Colors.ENDC}"))
    print(f"{Colors.OKCYAN}{line}{Colors.ENDC}")

def print_separator(char="-"):
    """打印分隔线"""
    width = get_terminal_width()
    print(f"{Colors.GRAY}{char * width}{Colors.ENDC}")

def format_time(seconds):
    """格式化时间显示"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"



# 预定义颜色列表，避免每次调用时重新创建
_COLOR_PALETTE = (
    Colors.FAIL,      # 红色
    Colors.WARNING,   # 黄色
    Colors.OKGREEN,   # 绿色
    Colors.OKCYAN,    # 青色
    Colors.OKBLUE,    # 蓝色
    Colors.HEADER     # 紫色
)
_COLOR_COUNT = len(_COLOR_PALETTE)

def get_colorful_text(text, color_offset=0):
    """为文本的每个字符应用不同的颜色（优化版）"""
    # 使用列表推导式和 join，比字符串拼接更高效
    return ''.join(
        _COLOR_PALETTE[(i + color_offset) % _COLOR_COUNT] + char
        for i, char in enumerate(text)
    ) + Colors.ENDC

def print_footer_text(color_offset=0):
    """打印底部彩色文字"""
    text = "XMU-Rollcall-Bot @ KrsMt"
    colored = get_colorful_text(text, color_offset)
    print(center_text(colored))


def print_dashboard(name, start_time, query_count, banner_frame=0, show_banner=True):
    """打印主仪表板"""
    c()
    print_banner()

    # 获取当前时间
    local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    # 获取问候语
    if time.localtime().tm_hour < 12 and time.localtime().tm_hour >= 5:
        greeting = "Good morning"
    elif time.localtime().tm_hour < 18 and time.localtime().tm_hour >= 12:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # 运行时间
    now = time.time()
    running_time = int(now - start_time)

    # 显示用户信息
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}{greeting}, {name}!{Colors.ENDC}\n")

    # 显示系统状态
    print(f"{Colors.BOLD}SYSTEM STATUS{Colors.ENDC}")
    print_separator()
    print(f"{Colors.BOLD}Current Time:{Colors.ENDC}    {Colors.OKCYAN}{local_time}{Colors.ENDC}")
    print(f"{Colors.BOLD}Running Time:{Colors.ENDC}    {Colors.OKGREEN}{format_time(running_time)}{Colors.ENDC}")
    print(f"{Colors.BOLD}Query Count:{Colors.ENDC}     {Colors.WARNING}{query_count}{Colors.ENDC}")

    # 显示监控状态
    print(f"\n{Colors.BOLD}ROLLCALL MONITOR{Colors.ENDC}")
    print_separator()
    print(f"{Colors.OKGREEN}Status:{Colors.ENDC} Active - Monitoring for new rollcalls...")
    print(f"{Colors.GRAY}Checking every {interval} second(s){Colors.ENDC}")
    print(f"{Colors.GRAY}Press Ctrl+C to exit{Colors.ENDC}\n")
    print_separator()

    # 显示底部彩色文字
    if show_banner:
        print()
        print_footer_text(banner_frame)



def print_login_status(message, is_success=True):
    """打印登录状态"""
    if is_success:
        print(f"{Colors.OKGREEN}[SUCCESS]{Colors.ENDC} {message}")
    else:
        print(f"{Colors.FAIL}[FAILED]{Colors.ENDC} {message}")

# 初始化
c()
print_banner()
print(f"\n{Colors.BOLD}Initializing XMU Rollcall Bot...{Colors.ENDC}\n")
print_separator()

print(f"\n{Colors.OKCYAN}[Step 1/3]{Colors.ENDC} Checking credentials...")

if os.path.exists(cookies):
    print(f"{Colors.OKCYAN}[Step 2/3]{Colors.ENDC} Found cached session, attempting to restore...")
    session_candidate = requests.Session()
    if l(session_candidate, cookies):
        profile = v(session_candidate)
        if profile:
            session = session_candidate
            print_login_status("Session restored successfully", True)
        else:
            print_login_status("Session expired, will re-login", False)
    else:
        print_login_status("Failed to load session", False)

if not session:
    print(f"{Colors.OKCYAN}[Step 2/3]{Colors.ENDC} Logging in with credentials...")
    time.sleep(2)
    session = xmulogin(type=3, username=USERNAME, password=pwd)
    if session:
        s(session, cookies)
        print_login_status("Login successful", True)
    else:
        print_login_status("Login failed. Please check your credentials", False)
        time.sleep(5)
        exit(1)

print(f"{Colors.OKCYAN}[Step 3/3]{Colors.ENDC} Fetching user profile...")
profile = session.get(f"{base_url}/api/profile", headers=headers).json()
name = profile["name"]
print_login_status(f"Welcome, {name}", True)

print(f"\n{Colors.OKGREEN}{Colors.BOLD}Initialization complete{Colors.ENDC}")
print(f"\n{Colors.GRAY}Starting monitor in 3 seconds...{Colors.ENDC}")
time.sleep(3)

# 主循环
temp_data = {'rollcalls': []}
query_count = 0
start_time = time.time()

# 首次打印完整界面（不显示底部文字，避免下移问题）
print_dashboard(name, start_time, query_count, 0, show_banner=False)

# 标志位：是否已经打印过底部文字
footer_initialized = False

# 记录需要更新的行位置（从屏幕顶部开始计数）
TIME_LINE = 10  # Current Time 所在行
RUNTIME_LINE = 11  # Running Time 所在行
QUERY_LINE = 12  # Query Count 所在行

# 底部文字起始行
FOOTER_LINE = 20  # 底部文字行

def update_status_line(line_num, label, value, color):
    """更新指定行的状态信息，不清屏"""
    # 隐藏光标
    sys.stdout.write("\033[?25l")
    # 保存光标位置
    sys.stdout.write("\033[s")
    # 移动到指定行
    sys.stdout.write(f"\033[{line_num};0H")
    # 清除整行
    sys.stdout.write("\033[2K")
    # 打印新内容
    sys.stdout.write(f"{Colors.BOLD}{label}{Colors.ENDC}    {color}{value}{Colors.ENDC}")
    # 恢复光标位置
    sys.stdout.write("\033[u")
    # 显示光标
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()

def update_footer_text():
    """更新底部彩色文字，不清屏，使用固定的彩虹颜色"""
    text = "XMU-Rollcall-Bot @ KrsMt"
    colored = get_colorful_text(text, 0)  # 固定使用颜色偏移0
    width = get_terminal_width()

    # 隐藏光标
    sys.stdout.write("\033[?25l")
    # 保存光标位置
    sys.stdout.write("\033[s")

    # 移动到底部文字行
    sys.stdout.write(f"\033[{FOOTER_LINE};0H")
    # 清除整行
    sys.stdout.write("\033[2K")

    # 计算居中
    text_len = len(text)  # 纯文本长度
    left_padding = (width - text_len) // 2
    # 打印内容
    sys.stdout.write(' ' * left_padding + colored)

    # 恢复光标位置
    sys.stdout.write("\033[u")
    # 显示光标
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()

try:
    # 预分配变量，减少循环内的对象创建
    _last_query_time = 0

    while True:
        try:
            time.sleep(0.1)  # 每0.1秒检查一次
        except KeyboardInterrupt:
            raise

        try:
            current_time = time.time()

            # 首次初始化底部文字
            if not footer_initialized:
                footer_initialized = True
                update_footer_text()

            # 每秒查询一次签到（优化：使用计数器而不是时间差计算）
            elapsed = int(current_time - start_time)
            if elapsed > _last_query_time:
                _last_query_time = elapsed
                data = session.get(rollcalls_url, headers=headers).json()
                query_count += 1

                # 只更新变化的信息，不清屏
                local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                running_time = format_time(elapsed)

                update_status_line(TIME_LINE, "Current Time:", local_time, Colors.OKCYAN)
                update_status_line(RUNTIME_LINE, "Running Time:", running_time, Colors.OKGREEN)
                update_status_line(QUERY_LINE, "Query Count: ", str(query_count), Colors.WARNING)


                # 检查签到数据
                if temp_data != data:
                    temp_data = data
                    if len(temp_data['rollcalls']) > 0:
                        # 有新签到时才清屏重绘
                        c()
                        width = get_terminal_width()
                        print(f"\n{Colors.WARNING}{Colors.BOLD}{'!' * width}{Colors.ENDC}")
                        print(center_text(f"{Colors.WARNING}{Colors.BOLD}NEW ROLLCALL DETECTED{Colors.ENDC}"))
                        print(f"{Colors.WARNING}{Colors.BOLD}{'!' * width}{Colors.ENDC}\n")
                        temp_data = a(temp_data, session)
                        print_separator("=")
                        print(f"\n{center_text(f'{Colors.GRAY}Press Ctrl+C to exit, continuing monitor...{Colors.ENDC}')}\n")
                        try:
                            time.sleep(3)
                        except KeyboardInterrupt:
                            # 在等待期间按 Ctrl+C，也直接跳到外层处理
                            raise
                        # 重新打印完整界面
                        print_dashboard(name, start_time, query_count, 0)
        except KeyboardInterrupt:
            # 在处理过程中按 Ctrl+C，跳到外层处理
            raise
        except Exception as e:
            # 其他异常，显示错误并退出
            c()
            print(f"\n{center_text(f'{Colors.FAIL}{Colors.BOLD}Error occurred:{Colors.ENDC} {str(e)}')}")
            print(f"{center_text(f'{Colors.GRAY}Exiting...{Colors.ENDC}')}\n")
            exit(1)
except KeyboardInterrupt:
    # 统一的退出处理
    c()
    print(f"\n{center_text(f'{Colors.WARNING}Shutting down gracefully...{Colors.ENDC}')}")
    print(f"{center_text(f'{Colors.GRAY}Total queries performed: {query_count}{Colors.ENDC}')}")
    print(f"{center_text(f'{Colors.GRAY}Total running time: {format_time(int(time.time() - start_time))}{Colors.ENDC}')}")
    print(f"\n{center_text(f'{Colors.OKGREEN}Goodbye{Colors.ENDC}')}\n")
    exit(0)

