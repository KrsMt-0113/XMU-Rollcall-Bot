`main.zip`：cli 版本

`main_gui.zip`：gui 版本（图形化界面）

`aiohttp.zip`：aiohttp 的 cli 版本

**使用步骤**

1. 下载到本地

   2. 解压后，在同目录下放置 `config.json` **文件**，以及新建一个 `cache` **文件夹**

      - 下载 `config.json` 后，用记事本打开，填写账号密码后保存在解压后的文件夹中；
     
        - 或者直接新建一个记事本，命名为 `config.json`，内容如下：
          ```json
          {
              "username":"_填入登录名，一般是学号_",
              "password":"_输入登录密码_",
              "sendkey": "_这里不动_",
              "latitude": 24.4378,
              "longitude": 118.0965
           }
          ```
        
        - 把后面两个数值分别改成签到地点的 **纬度** 和 **经度**。

      - 在解压后的文件夹里新建一个名为 `cache` 的空文件夹。

3. 双击 `.exe` 文件运行即可。
