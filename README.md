# `XMU Rollcall Bot v3.0.1`

> 对应目录: `XMU-Rollcall-Bot-CLI(v3)`

> **[下载工具](https://github.com/KrsMt-0113/XMU-Rollcall-Bot/releases)**
>
> **[移植文档](transplant.md)**
> 
> **[更新日志](ChangeLog.md)**
>
> [查询你所在学校/单位的 Tronclass apiUrl](Tronclass-URL-list/result.csv)

### ***此次更新基于大家使用过程中的所有反馈.***

<div align="center">
    <img src="XMU-Rollcall-Bot-CLI(v3)/screenshot.png" width="500">
</div>


> 为了进一步方便大家对厦门大学网站的各种开发，我制作了 `xmulogin` 包，大家可以直接 `pip install xmulogin` 使用。该包目前支持统一身份认证登录、教务系统登录和数字化教学平台登录。用法如下：
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

## 1. Selenium 启动慢、启动难

- 在这个版本，我们 **彻底抛弃** 了 Selenium。使用 Selenium 的初衷是因为我想偷懒，但事实证明代价是巨大的：我们收到许多关于 Chromedriver 无法被正常识别，或是无法正常连接至 Course 平台的反馈。

- **因此，我重写了登录模块，利用统一身份认证的接口直接填写表单登录。** 实测，在网络状况良好的情况下，登录时间在 **0.3秒** 左右。

    > 变快也是有代价的，详情见文档末尾 **警告** 部分的提示。

## 2. `config.json` 不会填，不能用

- `.json` 文件对一些不熟悉电脑操作的人甚至无法正确打开；编辑时也可能不小心引入中文标点符号导致文件读取错误；极端情况出现文件始终被系统以 `gbk` 编码打开，导致程序无法读取的问题。

- **这个版本，配置文件变为`.txt`后缀，并且直接在对应位置的四行内输入所需信息即可：**

- 1-4 行分别为：账号、密码、纬度、经度。以下为样例：

    ```aiignore
    12312341234567
    12345678abcdef
    24.479834
    118.089425
    ```
  
## 3. GUI 界面启动慢

- 从这个版本开始，**不再开发GUI版本。** CLI的界面更为简洁；但同时欢迎贡献美观的图形界面。

## 4. 其他学校适配难

- 在这个版本，适用于 XMU 的登录部分全部放在 `login.py` 中，其余部分 **只需** 改变代码首部的 `base_url` 即可。登录部分请按照 **自己的学校网站** 适配。

## 5. 高峰期遍历慢

- 由于之前使用 `aiohttp` 遍历的速度非常理想，当前版本已将该方法用于遍历。

## 现版本使用方法:

1. 填写 `info.txt`，按照上文所述的格式填写账号、密码、纬度、经度。

2. 直接运行 `main.py` 即可。

## ⚠️ 警告

- 如遇到 **登录失败** 的问题，请 **不要** 频繁重复运行软件，可能导致你的 **统一身份认证账号冻结。** 如果你的账号被冻结了，**几分钟后** 账号才会恢复正常。

- 如果你需要修改代码，请 **务必不要改变 `login.py` 中登录提交的表单内容**，否则会造成 **IP地址冻结**，目前看来这种冻结是 **永久性** 的。如果确实要尝试，请 **不要连接校园网。**

## To-do

- **[高优先级]** 集成二维码签到。

- **[低优先级]** 尝试枚举出二维码签到哈希值对应的原文内容。