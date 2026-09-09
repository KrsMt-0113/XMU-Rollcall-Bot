

<div align="center">

  <img src="https://socialify.git.ci/KrsMt-0113/XMU-Rollcall-Bot/image?font=JetBrains+Mono&forks=1&language=1&name=1&owner=1&pattern=Plus&stargazers=1&theme=Light" />

</div>

<div align="center">

  <img src="https://img.shields.io/github/directory-file-count/KrsMt-0113/XMU-Rollcall-Bot" />
  <img src="https://img.shields.io/github/languages/code-size/KrsMt-0113/XMU-Rollcall-Bot" />

</div>

---

> 由于事务繁忙，近期无计划更新本项目，用不了的话，那你就 **好好上课** 。
> 
> *but:*
> ```javascript
> 对于 iOS 用户，以下提供一种替代方案: Shortcut(快捷指令).
> 
> Shortcut 提供了在 Safari 浏览器中执行 JavaScript 脚本的能力, 可以在 Safari 中登录平台后执行脚本达到目的.
> 登录后需'请求桌面网站', 因为以下语句都在 base_url='https://lnt[.]xmu[.]edu[.]cn' 的前提下正常执行.
> 以下是示例脚本:
> 
> fetch('/api/radar/rollcalls')
>   .then(r=>r.text())
>   .then(completion)
>   .catch(e=>completion(String(e))); //获得签到列表
> 
> 获得到签到列表后, 提取出 rollcall_id, 此处可插入一段通知展示待签到课程.
> 
> fetch('/api/rollcall/__rollcall_id__/student_rollcalls') // __rollcall_id__ 处插入魔法变量, 下同
>   .then(r=>r.text())
>   .then(completion)
>   .catch(e=>completion(String(e))) //获得神秘数字
> 
> 以防最终签到失败, 可在此处插入通知展示神秘数字.
> 
> const deviceId=crypto.randomUUID(); //生成设备标识符
> fetch('/api/rollcall/__rollcall_id__/answer_number_rollcall',{
>   method:'PUT',
>   headers:{'Content-Type':'application/json'},
>   body:JSON.stringify({
>     'deviceId':String(deviceId),
>     'numberCode':String(__numbercode__) //此处插入魔法变量
>   })
> })
>   .then(r=>r.text())
>   .then(completion)
>   .catch(e=>completion(String(e)));
> 
> 完成仪式之后, 插入一条通知表明进度. 当然, 以上三段程式码可以合并, 省去利用快捷方式笨拙的方法提取变量的过程.
> 
> 对于 Android 用户, 据说也存在类似 Shortcut 的能力, 如有实现方法同上.
> 
> Windows / MacOS / Linux 等桌面操作系统, 在浏览器的开发者工具控制台执行以上语句即可.
> ```

---

以下是原文档.

---

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

## 使用方法

```bash
xmu config  # 配置账号。使用统一身份认证账号密码。
xmu switch  # 切换账号。
xmu start   # 启动监控。
```

## 其他

[数字化教学平台附件下载器](https://chromewebstore.google.com/detail/imannochailfofibofphcpmlddlbbhao?utm_source=item-share-cb)
