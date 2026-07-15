import click
import sys
from pathlib import Path
from xmulogin import xmulogin
from . import __version__
from .auth import CookieImportError, capture_browser_session, session_from_cookie_input
from .config import (
    load_config, save_config, is_config_complete, get_cookies_path,
    add_account, get_all_accounts, get_current_account, set_current_account,
    get_account_by_id, get_attendance_threshold, CONFIG_FILE, delete_account,
    perform_account_deletion
)
from .monitor import start_monitor, base_url, headers
from .utils import save_session, verify_session

# ANSI Color codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(f"{Colors.OKCYAN}{Colors.BOLD}XMU Rollcall Bot CLI v{__version__}{Colors.ENDC}")
        click.echo("\nUsage:")
        click.echo("  xmu config    Configure credentials and add accounts")
        click.echo("  xmu switch    Switch between accounts")
        click.echo("  xmu start     Start monitoring rollcalls")
        click.echo("  xmu auth      Import cookies or log in through a browser")
        click.echo("  xmu refresh   Refresh the login status")
        click.echo("  xmu --help    Show this message")

@cli.command()
def config():
    """配置账号：添加、删除账号"""
    click.echo(f"\n{Colors.BOLD}{Colors.OKCYAN}=== XMU Rollcall Configuration ==={Colors.ENDC}\n")

    current_config = load_config()

    def show_accounts():
        """显示账号列表"""
        accounts = get_all_accounts(current_config)
        if accounts:
            click.echo(f"{Colors.BOLD}Existing accounts:{Colors.ENDC}")
            current_account = get_current_account(current_config)
            for acc in accounts:
                current_marker = f" {Colors.OKGREEN}(current){Colors.ENDC}" if current_account and acc.get("id") == current_account.get("id") else ""
                click.echo(f"  {acc.get('id')}: {acc.get('name') or acc.get('username')}{current_marker}")
            click.echo()
        else:
            click.echo(f"{Colors.GRAY}No accounts configured.{Colors.ENDC}\n")

    def add_new_account():
        """添加新账号"""
        click.echo(f"{Colors.BOLD}Adding a new account...{Colors.ENDC}\n")

        # 输入新账号信息
        username = click.prompt(f"{Colors.BOLD}Username{Colors.ENDC}")
        password = click.prompt(f"{Colors.BOLD}Password{Colors.ENDC}", hide_input=False)

        # 验证登录
        click.echo(f"\n{Colors.OKCYAN}Validating credentials...{Colors.ENDC}")
        try:
            session = xmulogin(type=3, username=username, password=password)
            if session:
                click.echo(f"{Colors.OKGREEN}✓ Login successful!{Colors.ENDC}")

                # 获取用户姓名
                click.echo(f"{Colors.OKCYAN}Fetching user profile...{Colors.ENDC}")
                try:
                    profile = session.get(f"{base_url}/api/profile", headers=headers).json()
                    name = profile.get("name", "")
                    click.echo(f"{Colors.OKGREEN}✓ Welcome, {name}!{Colors.ENDC}")
                except Exception:
                    click.echo(f"{Colors.WARNING}⚠ Could not fetch profile, using username as name{Colors.ENDC}")
                    name = username

                # 添加账号
                try:
                    account_id = add_account(current_config, username, password, name)
                    save_config(current_config)

                    click.echo(f"{Colors.OKGREEN}✓ Account added successfully! (ID: {account_id}){Colors.ENDC}")
                    click.echo(f"{Colors.GRAY}Configuration file: {CONFIG_FILE}{Colors.ENDC}\n")
                except RuntimeError as e:
                    click.echo(f"{Colors.FAIL}✗ Failed to save configuration: {str(e)}{Colors.ENDC}")
                    click.echo(f"{Colors.WARNING}Tip: In sandboxed environments (like a-Shell), set environment variable:{Colors.ENDC}")
                    click.echo("  export XMU_ROLLCALL_CONFIG_DIR=~/Documents/.xmu_rollcall")
            else:
                click.echo(f"{Colors.FAIL}✗ Login failed. Please check your credentials.{Colors.ENDC}")
        except Exception as e:
            click.echo(f"{Colors.FAIL}✗ Error during login validation: {str(e)}{Colors.ENDC}")
            click.echo(
                f"{Colors.WARNING}Fallback: use `xmu auth import` or "
                f"`xmu auth browser`.{Colors.ENDC}"
            )

    def delete_existing_account():
        """删除账号"""
        accounts = get_all_accounts(current_config)
        if not accounts:
            click.echo(f"{Colors.WARNING}No accounts to delete.{Colors.ENDC}\n")
            return

        show_accounts()

        # 让用户选择要删除的账号
        valid_ids = [str(acc.get("id")) for acc in accounts]
        selected_id = click.prompt(
            f"{Colors.BOLD}Enter account ID to delete{Colors.ENDC}",
            type=click.Choice(valid_ids, case_sensitive=False)
        )

        selected_id = int(selected_id)
        selected_account = get_account_by_id(current_config, selected_id)

        if selected_account:
            # 确认删除
            confirm = click.prompt(
                f"{Colors.WARNING}Are you sure you want to delete account '{selected_account.get('name') or selected_account.get('username')}' (ID: {selected_id})?{Colors.ENDC}",
                type=click.Choice(['y', 'n'], case_sensitive=False),
                default='n'
            )

            if confirm.lower() == 'y':
                # 执行删除
                success, cookies_to_delete, cookies_to_rename = delete_account(current_config, selected_id)

                if success:
                    # 保存配置
                    save_config(current_config)

                    # 处理cookies文件
                    perform_account_deletion(cookies_to_delete, cookies_to_rename)

                    click.echo(f"{Colors.OKGREEN}✓ Account deleted successfully!{Colors.ENDC}")

                    # 显示ID变更提示
                    if cookies_to_rename:
                        click.echo(f"{Colors.GRAY}Note: Account IDs have been re-assigned.{Colors.ENDC}")
                    click.echo()
                else:
                    click.echo(f"{Colors.FAIL}✗ Failed to delete account.{Colors.ENDC}\n")
            else:
                click.echo(f"{Colors.GRAY}Deletion cancelled.{Colors.ENDC}\n")
        else:
            click.echo(f"{Colors.FAIL}✗ Account not found.{Colors.ENDC}\n")

    # 主循环
    while True:
        show_accounts()

        click.echo(f"{Colors.BOLD}Choose an action:{Colors.ENDC}")
        click.echo(f"  {Colors.OKCYAN}n{Colors.ENDC} - Add new account")
        click.echo(f"  {Colors.OKCYAN}d{Colors.ENDC} - Delete account")
        click.echo(f"  {Colors.OKCYAN}t{Colors.ENDC} - Set attendance threshold")
        click.echo(f"  {Colors.OKCYAN}q{Colors.ENDC} - Quit")

        action = click.prompt(
            f"\n{Colors.BOLD}Action{Colors.ENDC}",
            type=click.Choice(['n', 'd', 't', 'q'], case_sensitive=False),
            default='q'
        )

        click.echo()

        if action.lower() == 'n':
            add_new_account()
        elif action.lower() == 'd':
            delete_existing_account()
        elif action.lower() == 't':
            current_threshold = get_attendance_threshold(current_config)
            threshold = click.prompt(
                f"{Colors.BOLD}Attendance threshold (0 to 1){Colors.ENDC}",
                type=click.FloatRange(0, 1),
                default=current_threshold,
            )
            current_config["attendance_threshold"] = threshold
            save_config(current_config)
            click.echo(
                f"{Colors.OKGREEN}✓ Attendance threshold set to "
                f"{threshold:.0%}.{Colors.ENDC}\n"
            )
        elif action.lower() == 'q':
            # 退出前显示最终账号列表
            accounts = get_all_accounts(current_config)
            if accounts:
                click.echo(f"{Colors.BOLD}Final account list:{Colors.ENDC}")
                current_account = get_current_account(current_config)
                for acc in accounts:
                    current_marker = f" {Colors.OKGREEN}(current){Colors.ENDC}" if current_account and acc.get("id") == current_account.get("id") else ""
                    click.echo(f"  {acc.get('id')}: {acc.get('name') or acc.get('username')}{current_marker}")
                click.echo(f"\n{Colors.GRAY}You can run: {Colors.BOLD}xmu switch{Colors.ENDC} to switch between accounts")
                click.echo(f"{Colors.GRAY}You can run: {Colors.BOLD}xmu start{Colors.ENDC} to start monitoring")
            break

@cli.command()
@click.option(
    "--attendance-threshold",
    type=click.FloatRange(0, 1),
    default=None,
    help="Fraction of classmates who must sign first (default: configured 20%).",
)
def start(attendance_threshold):
    """启动签到监控"""
    # 加载配置
    config_data = load_config()

    # 检查配置是否完整
    if not is_config_complete(config_data):
        click.echo(f"{Colors.FAIL}✗ Configuration incomplete!{Colors.ENDC}")
        click.echo(f"Please run: {Colors.BOLD}xmu config{Colors.ENDC}")
        sys.exit(1)

    # 获取当前账号
    current_account = get_current_account(config_data)
    if attendance_threshold is None:
        attendance_threshold = get_attendance_threshold(config_data)
    click.echo(f"{Colors.OKCYAN}Using account: {current_account.get('name') or current_account.get('username')} (ID: {current_account.get('id')}){Colors.ENDC}")
    click.echo(
        f"{Colors.OKCYAN}Attendance threshold: "
        f"{attendance_threshold:.0%}{Colors.ENDC}"
    )

    # 启动监控
    try:
        start_monitor(current_account, attendance_threshold)
    except KeyboardInterrupt:
        click.echo(f"\n{Colors.WARNING}Shutting down...{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        click.echo(f"\n{Colors.FAIL}Error: {str(e)}{Colors.ENDC}")
        sys.exit(1)

@cli.command()
def refresh():
    """清除当前账号的登录缓存"""
    config_data = load_config()
    current_account = get_current_account(config_data)

    if not current_account:
        click.echo(f"{Colors.FAIL}✗ No account configured!{Colors.ENDC}")
        click.echo(f"Please run: {Colors.BOLD}xmu config{Colors.ENDC}")
        sys.exit(1)

    account_id = current_account.get("id")
    cookies_path = get_cookies_path(account_id)
    try:
        click.echo(f"\n{Colors.WARNING}Deleting cookies for account {account_id} ({current_account.get('name')})...{Colors.ENDC}")
        # delete cookies file
        import os
        if os.path.exists(cookies_path):
            os.remove(cookies_path)
            click.echo(f"{Colors.OKGREEN}✓ Cookies deleted successfully.{Colors.ENDC}")
        else:
            click.echo(f"{Colors.GRAY}No cookies file found to delete.{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        click.echo(f"{Colors.FAIL}✗ Failed to delete cookies: {str(e)}{Colors.ENDC}")
        sys.exit(1)


@cli.command()
def switch():
    """切换当前使用的账号"""
    click.echo(f"\n{Colors.BOLD}{Colors.OKCYAN}=== Switch Account ==={Colors.ENDC}\n")

    config_data = load_config()
    accounts = get_all_accounts(config_data)

    if not accounts:
        click.echo(f"{Colors.FAIL}✗ No accounts configured!{Colors.ENDC}")
        click.echo(f"Please run: {Colors.BOLD}xmu config{Colors.ENDC}")
        sys.exit(1)

    current_account = get_current_account(config_data)
    current_id = current_account.get("id") if current_account else None

    # 显示账号列表
    click.echo(f"{Colors.BOLD}Available accounts:{Colors.ENDC}")
    for acc in accounts:
        current_marker = f" {Colors.OKGREEN}(current){Colors.ENDC}" if acc.get("id") == current_id else ""
        click.echo(f"  {acc.get('id')}: {acc.get('name') or acc.get('username')}{current_marker}")

    click.echo()

    # 让用户选择账号
    valid_ids = [str(acc.get("id")) for acc in accounts]
    selected_id = click.prompt(
        f"{Colors.BOLD}Enter account ID to switch to{Colors.ENDC}",
        type=click.Choice(valid_ids, case_sensitive=False)
    )

    selected_id = int(selected_id)
    selected_account = get_account_by_id(config_data, selected_id)

    if selected_account:
        set_current_account(config_data, selected_id)
        save_config(config_data)
        click.echo(f"\n{Colors.OKGREEN}✓ Switched to account: {selected_account.get('name') or selected_account.get('username')} (ID: {selected_id}){Colors.ENDC}")
        click.echo(f"{Colors.GRAY}You can now run: {Colors.BOLD}xmu start{Colors.ENDC}")
    else:
        click.echo(f"{Colors.FAIL}✗ Account not found!{Colors.ENDC}")
        sys.exit(1)


def _persist_authenticated_session(config_data, session, account_id=None):
    profile = verify_session(session)
    if not profile:
        raise RuntimeError(
            "The imported session could not access /api/profile. "
            "Check that the cookies belong to lnt.xmu.edu.cn and are not expired."
        )

    account = None
    explicit_account = account_id is not None
    if account_id is not None:
        account = get_account_by_id(config_data, account_id)
        if account is None:
            raise RuntimeError(f"Account ID {account_id} does not exist.")
    else:
        account = get_current_account(config_data)

    name = profile.get("name") or profile.get("nickname") or "Cookie account"
    profile_identity = (
        profile.get("user_no")
        or profile.get("username")
        or profile.get("email")
    )
    username = profile_identity or (account and account.get("username")) or name

    if (
        account is not None
        and not explicit_account
        and profile_identity
        and account.get("username")
        and str(account["username"]) != str(profile_identity)
    ):
        account = None

    if account is None:
        account_id = add_account(config_data, username, "", name)
        account = get_account_by_id(config_data, account_id)
        set_current_account(config_data, account_id)
    else:
        account_id = account["id"]
        account["name"] = name
        if not account.get("username"):
            account["username"] = username

    cookies_path = get_cookies_path(account_id)
    if not save_session(session, cookies_path):
        raise RuntimeError(f"Failed to save cookies to {cookies_path}.")
    save_config(config_data)
    return account, cookies_path


@cli.group()
def auth():
    """Authenticate with imported cookies or an interactive browser."""


@auth.command(name="import")
@click.option(
    "--file",
    "file_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Read cookies from a JSON or text file instead of prompting.",
)
@click.option("--account-id", type=int, help="Replace cookies for this account ID.")
def import_cookies(file_path, account_id):
    """Import a JSON cookie export or raw Cookie header."""
    try:
        if file_path:
            cookie_input = file_path.read_text(encoding="utf-8")
        else:
            cookie_input = click.prompt(
                "Paste cookie JSON or a raw Cookie header",
                hide_input=True,
            )
        session = session_from_cookie_input(cookie_input)
        account, cookies_path = _persist_authenticated_session(
            load_config(), session, account_id
        )
    except (CookieImportError, OSError, RuntimeError) as exc:
        raise click.ClickException(str(exc))

    click.echo(
        f"{Colors.OKGREEN}✓ Cookies imported for "
        f"{account.get('name') or account.get('username')}.{Colors.ENDC}"
    )
    click.echo(f"{Colors.GRAY}Cookie cache: {cookies_path}{Colors.ENDC}")


@auth.command(name="browser")
@click.option("--account-id", type=int, help="Replace cookies for this account ID.")
@click.option(
    "--timeout",
    type=click.IntRange(30, 1800),
    default=300,
    show_default=True,
    help="Seconds to wait for browser login.",
)
def browser_login(account_id, timeout):
    """Open Chromium, wait for login, and capture the resulting cookies."""
    click.echo("Opening Chromium. Complete XMU login in the browser window...")
    try:
        session = capture_browser_session(timeout)
        account, cookies_path = _persist_authenticated_session(
            load_config(), session, account_id
        )
    except RuntimeError as exc:
        raise click.ClickException(str(exc))

    click.echo(
        f"{Colors.OKGREEN}✓ Browser login captured for "
        f"{account.get('name') or account.get('username')}.{Colors.ENDC}"
    )
    click.echo(f"{Colors.GRAY}Cookie cache: {cookies_path}{Colors.ENDC}")


if __name__ == '__main__':
    cli()
