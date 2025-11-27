import shutil

def get_terminal_width():
    """获取终端宽度"""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80

width = get_terminal_width()
print(f"Terminal width: {width}")

# 测试当前逻辑
left_width = max(12, width // 5)
middle_width = max(20, (width * 2) // 5)
right_width = width - left_width - middle_width

print(f"Left width: {left_width}")
print(f"Middle width: {middle_width}")
print(f"Right width: {right_width}")
print(f"Total: {left_width + middle_width + right_width}")
print(f"Expected: {width}")
print(f"Difference: {(left_width + middle_width + right_width) - width}")

# 测试实际填充
def pad_to_width(content, target_width):
    content_len = len(content)
    if content_len >= target_width:
        return content[:target_width]
    padding_total = target_width - content_len
    padding_left = padding_total // 2
    padding_right = padding_total - padding_left
    return ' ' * padding_left + content + ' ' * padding_right

left_content = "12:34:56"
middle_content = "Good afternoon, User"
right_content = "Active | Up: 5m 23s | Q: 100"

left_part = pad_to_width(left_content, left_width)
middle_part = pad_to_width(middle_content, middle_width)
right_part = pad_to_width(right_content, right_width)

print(f"\nActual lengths:")
print(f"Left part: {len(left_part)}")
print(f"Middle part: {len(middle_part)}")
print(f"Right part: {len(right_part)}")
print(f"Total: {len(left_part) + len(middle_part) + len(right_part)}")

# 打印状态栏
status_bar = f"\033[44m\033[97m{left_part}\033[0m\033[46m\033[30m{middle_part}\033[0m\033[42m\033[97m{right_part}\033[0m"
print(f"\nStatus bar:")
print(status_bar)
print(f"Length check: {len(left_part + middle_part + right_part)} == {width}")

