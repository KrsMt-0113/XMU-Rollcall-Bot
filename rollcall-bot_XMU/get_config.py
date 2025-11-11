import os
import sys
import json

def resource_path(rel_path: str) -> str:
    """兼容直接运行与 PyInstaller 打包后的资源路径"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel_path)

def get_config_path() -> str:
    candidates = [
        resource_path("config.json"),
        resource_path(os.path.join("rollcall-bot_XMU", "config.json")),
        resource_path(os.path.join("Resources", "config.json")),  # 有时放到 Contents/Resources
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),  # 直接运行时
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"config.json not found. tried:\n" + "\n".join(candidates))