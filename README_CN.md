

<div align="center">

  <img src="https://socialify.git.ci/KrsMt-0113/XMU-Rollcall-Bot/image?font=JetBrains+Mono&forks=1&language=1&name=1&owner=1&pattern=Plus&stargazers=1&theme=Light" />

</div>

<div align="center">

  <img src="https://img.shields.io/github/directory-file-count/KrsMt-0113/XMU-Rollcall-Bot" />
  <img src="https://img.shields.io/github/languages/code-size/KrsMt-0113/XMU-Rollcall-Bot" />

</div>

[English](README.md)

[使用手册](https://krsmt.notion.site/cli-doc)

> [!WARNING]
> 2026-05-12 之前的登录方式已被弃用。使用 `pip install -U xmulogin` 更新相关组件到最新版本。
>
> 2026-05-15 ~登录组件出现新的问题，等待进一步排查修复。~
>
> 2026-05-15 降级`xmulogin`组件以恢复正常: `pip install xmulogin==1.0.0`

## 快速开始

```bash
pip install xmu-rollcall-cli
```

如需使用桌面浏览器登录回退：

```bash
pip install 'xmu-rollcall-cli[browser]'
playwright install chromium
```

浏览器登录回退需要 Python 3.8 或更高版本。

## 使用方法

```bash
xmu config  # 配置账号。使用统一身份认证账号密码。
xmu switch  # 切换账号。
xmu start   # 启动监控，默认等待班级 20% 的同学完成签到。
xmu auth import --file cookies.json  # 导入已登录的 Cookie。
xmu auth browser  # 打开官方登录页并捕获登录后的 Cookie。
```

现已支持自主点名。可用 `xmu start --attendance-threshold 0` 关闭延迟签到。
移动端或沙盒环境无法拉起浏览器时请使用 Cookie 导入。Cookie 等同于登录凭据，
请勿上传到 issue 或提供给他人。

## 其他

[数字化教学平台附件下载器](https://chromewebstore.google.com/detail/imannochailfofibofphcpmlddlbbhao?utm_source=item-share-cb)
