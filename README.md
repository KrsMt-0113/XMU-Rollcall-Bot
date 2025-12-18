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

### ***此次更新基于大家使用过程中的所有反馈.***

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

1. 填写 `info.txt`，按照上文所述的格式填写账号、密码、~~纬度、经度。~~ 现版本经纬度将自动计算。

2. 直接运行 `main.py` 即可。

## ⚠️ 警告

- 如遇到 **登录失败** 的问题，请 **不要** 频繁重复运行软件，可能导致你的 **统一身份认证账号冻结。** 如果你的账号被冻结了，**几分钟后** 账号才会恢复正常。

- 如果你需要修改代码，请 **务必不要改变 `login.py` 中登录提交的表单内容**，否则会造成 **IP地址冻结**，目前看来这种冻结是 **永久性** 的。如果确实要尝试，请 ~~**不要连接校园网。**~~(经我测试，校园网的 ip 是白名单，随便造)。
