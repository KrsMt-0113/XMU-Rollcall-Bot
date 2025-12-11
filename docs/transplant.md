# 移植文档

前往 [该文件夹](../xmu-rollcall-cli) 下载本工具的最新版本源代码。

结构说明:
```aiignore
- cli.py               # 命令行入口
- config.py            # 配置文件读取与写入
- monitor.py           # 监控主循环
- rollcall_handler.py  # 签到处理逻辑
- utils.py             # 工具函数
- verify.py            # 签到执行逻辑
```

1. 登录方面采用适用于厦门大学的统一身份认证方式即 `xmulogin` 库，请为自己学校重新编写。

2. 如需上传至PyPI，请修改相关信息，包括作者、README、包名称、版本号等。

3. 如需打包为可执行文件，请前往 [这里](../legacy/v3.0.1) 下载代码并使用 `PyInstaller` 打包。

4. 请修改所有代码中的 `base_url`。