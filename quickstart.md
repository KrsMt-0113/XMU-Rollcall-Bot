# 快速开始

1. 项目概况

    `main.py`: 主程序。主要处理登录与签到的监控。

    `parse_rollcalls.py`: 用于解析签到任务的模块。

    `send_code.py`: 用于遍历、发送验证码的模块。

    `config.json`: 配置文件。存储用户账号信息与[Server酱](https://sc3.ft07.com/)的sendkey。
   
    > `main.py`登录，启动监控 → 监测到签到任务 → `parse_rollcalls.py`解析任务信息 → `send_code.py`遍历并发送签到码 → 完成签到。

    `gui.py`: 图形界面模块。

    `main_gui.py`: 图形界面主程序。

2. 环境准备

   - `Python`版本: 建议 `3.13.*`
    
   - 安装依赖: `pip install -r requirements.txt`

   - 网络环境: 可能需要 VPN，`Selenium`存在无法直连的情况。
   
3. 配置文件

    在 `config.json` 中的对应位置填入账号、密码、Server酱的sendkey（可不填）。

    ```json
    {
        "username": "账号",
        "password": "密码",
        "sendkey": "sendkey"
    }
    ```

    > 账号密码请确认填写准确。
   
4. 运行程序
    
    CLI 模式：直接运行 `main.py` 即可。
    GUI 模式：运行 'main_gui.py' 即可。
