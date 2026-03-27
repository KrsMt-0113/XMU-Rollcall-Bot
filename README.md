### 注意：2026年发布的新版本由于100%由AI开发，遇到了大量bug，当前已经回退至2025年底的2.1+版本，若你的当前版本可以正常使用，则无需回退。

<div align="center">

  <img src="https://socialify.git.ci/KrsMt-0113/XMU-Rollcall-Bot/image?font=JetBrains+Mono&forks=1&language=1&name=1&owner=1&pattern=Plus&stargazers=1&theme=Light" />

</div>

<div align="center">

  <img src="https://img.shields.io/github/downloads/KrsMt-0113/XMU-Rollcall-Bot/total.svg" />
  <img src="https://img.shields.io/github/directory-file-count/KrsMt-0113/XMU-Rollcall-Bot" />
  <img src="https://img.shields.io/github/languages/code-size/KrsMt-0113/XMU-Rollcall-Bot" />

</div>


> **[移植文档](docs/transplant.md)**
>
> **[在各操作系统(iOS, Android, Windows, Linux) 运行本项目](https://krsmt.notion.site/cli-doc)**
>
> [查询你所在学校/单位的 Tronclass apiUrl](Tronclass-URL-list/result.csv)

## Features

- 支持自动登录厦门大学统一身份认证系统、教务系统和数字化教学平台

- 支持自动爆破数字签到、自动计算雷达签到

- 未来支持远程扫码签到轻便解决方案*

*\* 当前二维码代签普遍采用备用机交给同学、账号登录同学手机的方法，该解决方案为生成一个临时链接，将该临时链接发给在教室的同学即可在网页中扫码实现签到，无需切换账号。该功能可配合Server酱等推送服务使用，在检测到新签到时自动将临时链接发送至钉钉、企业微信群或其他通知渠道中。*

> 为了进一步方便大家对厦门大学网站的各种开发，我制作了 `xmulogin` SDK 并上传至 PyPi，可直接 `pip install xmulogin` 使用。目前支持统一身份认证登录、教务系统登录和数字化教学平台登录。用法如下：
> 
> ```python
> from xmulogin import xmulogin
> 
> # 登录统一身份认证系统 (type=1)
> session = xmulogin(type=1, username="your_username", password="your_password")
> # 登录教务系统 (type=2)
> session = xmulogin(type=2, username="your_username", password="your_password")
> # 登录数字化教学平台 (type=3)
> session = xmulogin(type=3, username="your_username", password="your_password")
>```
>

## 现版本使用方法:

1. 填写 `info.txt`，按照上文所述的格式填写账号、密码， 直接运行主程序即可。

2. 前往 (此处)[https://krsmt.notion.site/cli-doc], 了解在各种设备上使用该工具的指令语句。

## ⚠️ 警告

- 如遇到 **登录失败** 的问题，请 **不要** 频繁重复运行软件，可能导致你的 **统一身份认证账号冻结。** 如果你的账号被冻结了，**几分钟后** 账号才会恢复正常。