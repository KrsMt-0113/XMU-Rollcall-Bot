

<div align="center">

  <img src="https://socialify.git.ci/KrsMt-0113/XMU-Rollcall-Bot/image?font=JetBrains+Mono&forks=1&language=1&name=1&owner=1&pattern=Plus&stargazers=1&theme=Light" />

</div>

<div align="center">

  <img src="https://img.shields.io/github/directory-file-count/KrsMt-0113/XMU-Rollcall-Bot" />
  <img src="https://img.shields.io/github/languages/code-size/KrsMt-0113/XMU-Rollcall-Bot" />

</div>

[简体中文](README_CN.md)

> [!WARNING]
> 2026-05-12 Previous login method has been deprecated. Update with `pip install -U xmulogin` to get the latest version.
>
> 2026-05-15 ~New issue with login process. Stay tuned for updates.~
>
> 2026-05-15 Downgrade `xmulogin` with `pip install xmulogin==1.0.0` to fix it.

## Install

```bash
pip install xmu-rollcall-cli
```

For the optional interactive browser-login fallback:

```bash
pip install 'xmu-rollcall-cli[browser]'
playwright install chromium
```

Browser login requires Python 3.8 or newer.

## Usage

```bash
xmu config  # configure your account. support multiple accounts.
xmu switch  # switch between accounts.
xmu start   # start the monitor; waits for 20% attendance by default.
xmu auth import --file cookies.json  # import an authenticated cookie export.
xmu auth browser  # open the official login page and capture its cookies.
```

Manual self-registration rollcalls are supported. Use
`xmu start --attendance-threshold 0` to disable the attendance delay. Never
share cookie files; they grant access to your active session.

## Other

[XMU File Downloader](https://chromewebstore.google.com/detail/imannochailfofibofphcpmlddlbbhao?utm_source=item-share-cb)
