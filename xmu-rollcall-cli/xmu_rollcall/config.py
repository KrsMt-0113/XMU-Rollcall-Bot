import os
import json
from pathlib import Path

def get_config_dir():
    """
    获取配置目录路径，支持沙盒环境（如 a-Shell）
    优先级：
    1. 环境变量 XMU_ROLLCALL_CONFIG_DIR
    2. 用户主目录下的 .xmu_rollcall（如果可访问）
    3. 当前工作目录下的 .xmu_rollcall（沙盒环境备用方案）
    """
    # 优先使用环境变量指定的路径
    if env_path := os.environ.get("XMU_ROLLCALL_CONFIG_DIR"):
        return Path(env_path)

    # 尝试使用用户主目录
    try:
        home_config_dir = Path.home() / ".xmu_rollcall"
        # 测试是否可以创建目录（检测沙盒权限）
        home_config_dir.mkdir(parents=True, exist_ok=True)
        # 测试是否可以写入文件
        test_file = home_config_dir / ".test_write"
        try:
            test_file.touch()
            test_file.unlink()
            return home_config_dir
        except (OSError, PermissionError):
            pass
    except (OSError, PermissionError, RuntimeError):
        pass

    # 降级到当前工作目录（适用于沙盒环境）
    return Path.cwd() / ".xmu_rollcall"

CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "username": "",
    "password": "",
    "latitude": 0.0,
    "longitude": 0.0
}

def ensure_config_dir():
    """确保配置目录存在"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        raise RuntimeError(f"无法创建配置目录 {CONFIG_DIR}: {e}\n提示：可以设置环境变量 XMU_ROLLCALL_CONFIG_DIR 指定配置目录位置")

def load_config():
    """加载配置文件"""
    ensure_config_dir()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """保存配置文件"""
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def is_config_complete(config):
    """检查配置是否完整"""
    required_fields = ["username", "password", "latitude", "longitude"]
    return all(config.get(field) for field in required_fields)

def get_cookies_path():
    """获取cookies文件路径"""
    ensure_config_dir()
    return str(CONFIG_DIR / "cookies.json")

