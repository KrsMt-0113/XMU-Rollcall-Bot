# xmu-rollcall-cli

A command-line tool for monitoring and auto-answering Tronclass rollcalls at Xiamen University.

> This project is intended for personal learning and automation convenience. Use it at your own risk and comply with your school's rules.

## Features

- Login with XMU unified authentication through `xmulogin`
- Continuous rollcall polling (1-second interval)
- Automatic handling for:
  - Number rollcalls (fetch number code and answer directly)
  - Radar rollcalls (location solving)
  - Manual self-registration rollcalls
- Wait until 20% of the class has signed before answering (configurable)
- Multi-account management in one local config
- Session cookie cache and refresh support
- Cookie import and interactive browser-login fallbacks

## Installation

Install from PyPI:

```bash
pip install xmu-rollcall-cli
```

After installation, these command aliases are available:

- `xmu`
- `xmu-rollcall-cli`
- `XMUrollcall-cli`

## Quick Start

1. Configure at least one account:

```bash
xmu config
```

2. (Optional) Switch active account:

```bash
xmu switch
```

3. Start monitoring:

```bash
xmu start
```

4. If session becomes invalid, refresh cookies:

```bash
xmu refresh
```

By default the bot waits until at least 20% of students have signed. Override
the configured value for one run with:

```bash
xmu start --attendance-threshold 0.3
```

Use `0` to disable the delay. The bot keeps waiting when the attendance API is
unavailable, so it does not sign early by accident.

## Login fallbacks

If password login is challenged, import cookies from a JSON export or raw
`Cookie` header. The file may contain a `{name: value}` object, a list of
browser cookie objects, or `{"cookies": [...]}`:

```bash
xmu auth import --file cookies.json
```

Without `--file`, the command securely prompts for pasted cookie content. Never
post your cookies in an issue or send them to another person.

On a desktop, the optional browser flow opens the official XMU/TronClass login
page and captures the authenticated cookies after you finish any login or QR
steps shown there:

```bash
pip install 'xmu-rollcall-cli[browser]'
playwright install chromium
xmu auth browser
```

The browser fallback requires Python 3.8 or newer. Core CLI and cookie import
support remain available on Python 3.7.

Browser launching may be unavailable in mobile shells and sandboxed
environments; use cookie import there.

## Commands

- `xmu config` - Add/delete accounts and set current account
- `xmu switch` - Switch the current account
- `xmu start` - Start rollcall monitoring loop
- `xmu auth import` - Import an authenticated browser cookie export
- `xmu auth browser` - Log in through an interactive Chromium window
- `xmu refresh` - Remove cached cookies for current account
- `xmu --help` - Show help

## Configuration

The package stores local data in a `.xmu_rollcall` directory:

1. `XMU_ROLLCALL_CONFIG_DIR` (if set)
2. `~/.xmu_rollcall` (default)
3. `./.xmu_rollcall` (fallback when home is not writable)

Main files:

- `config.json`: account list and selected account
- `<account_id>.json`: cached cookies per account

Example (custom config directory):

```bash
export XMU_ROLLCALL_CONFIG_DIR="$HOME/Documents/.xmu_rollcall"
```

## Limitations

- QR code rollcalls are currently **not supported**.
- This tool depends on Tronclass/XMU API behavior and may break if upstream endpoints change.

## Supported Python Versions

- Python 3.7+

## Project Links

- Homepage: https://github.com/KrsMt-0113/XMU-Rollcall-Bot
- Issues: https://github.com/KrsMt-0113/XMU-Rollcall-Bot/issues

## License

MIT License
