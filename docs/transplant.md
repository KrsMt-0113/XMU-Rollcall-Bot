# 移植文档

前往 [该文件夹](XMU-Rollcall-Bot-CLI(v3)) 下载本工具的最新版本源代码。

结构说明:
```aiignore
- main.py          # 主程序入口
- login.py         # 登录模块
- misc.py          # 其他辅助功能
- verify.py        # 签到模块
- info.txt         # 配置文件，填写账号、密码、纬度、经度
- requirements.txt # 依赖列表
```

1. 请根据具体情况修改 `login.py`,以适配不同学校的登录方式；

2. 请修改 `main.py` 与 `verify.py` 中的 `base_url` 变量，以适配不同学校的 Tronclass 平台。