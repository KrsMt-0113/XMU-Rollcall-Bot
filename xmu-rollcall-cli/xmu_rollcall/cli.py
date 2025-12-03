import click
import sys
from xmulogin import xmulogin
from .config import load_config, save_config, is_config_complete
from .monitor import start_monitor

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
    """XMU Rollcall Bot CLI - Automated rollcall monitoring and answering"""
    if ctx.invoked_subcommand is None:
        click.echo(f"{Colors.OKCYAN}{Colors.BOLD}XMU Rollcall Bot CLI v3.1.0{Colors.ENDC}")
        click.echo(f"\nUsage:")
        click.echo(f"  XMUrollcall-cli config    Configure credentials and location")
        click.echo(f"  XMUrollcall-cli start     Start monitoring rollcalls")
        click.echo(f"  XMUrollcall-cli --help      Show this message")

@cli.command()
def config():
    """配置账号密码和位置信息"""
    click.echo(f"\n{Colors.BOLD}{Colors.OKCYAN}=== XMU Rollcall Configuration ==={Colors.ENDC}\n")

    current_config = load_config()

    # 显示当前配置
    if any(current_config.values()):
        click.echo(f"{Colors.GRAY}Current configuration:{Colors.ENDC}")
        click.echo(f"  Username: {current_config.get('username', '(not set)')}")
        click.echo(f"  Password: {'*' * len(current_config.get('password', '')) if current_config.get('password') else '(not set)'}")
        click.echo(f"  Latitude: {current_config.get('latitude', '(not set)')}")
        click.echo(f"  Longitude: {current_config.get('longitude', '(not set)')}")
        click.echo()

    # 输入新配置
    username = click.prompt(f"{Colors.BOLD}Username{Colors.ENDC}",
                           default=current_config.get('username', ''),
                           show_default=True if current_config.get('username') else False)

    password = click.prompt(f"{Colors.BOLD}Password{Colors.ENDC}",
                           default=current_config.get('password', ''),
                           show_default=True if current_config.get('password') else False)

    latitude = click.prompt(f"{Colors.BOLD}Latitude{Colors.ENDC}",
                            default=current_config.get('latitude', ''),
                            show_default=True if current_config.get('latitude') else False,
                            type=float)

    longitude = click.prompt(f"{Colors.BOLD}Longitude{Colors.ENDC}",
                             default=current_config.get('longitude', ''),
                             show_default=True if current_config.get('longitude') else False,
                             type=float)

    # 验证登录
    click.echo(f"\n{Colors.OKCYAN}Validating credentials...{Colors.ENDC}")
    try:
        session = xmulogin(type=3, username=username, password=password)
        if session:
            click.echo(f"{Colors.OKGREEN}✓ Login successful!{Colors.ENDC}")

            # 保存配置
            new_config = {
                "username": username,
                "password": password,
                "latitude": latitude,
                "longitude": longitude
            }

            try:
                save_config(new_config)

                # 显示配置文件保存位置
                from .config import CONFIG_FILE
                click.echo(f"{Colors.OKGREEN}✓ Configuration saved successfully!{Colors.ENDC}")
                click.echo(f"{Colors.GRAY}Configuration file: {CONFIG_FILE}{Colors.ENDC}\n")
                click.echo(f"You can now run: {Colors.BOLD}XMUrollcall-cli start{Colors.ENDC}")
            except RuntimeError as e:
                click.echo(f"{Colors.FAIL}✗ Failed to save configuration: {str(e)}{Colors.ENDC}")
                click.echo(f"{Colors.WARNING}Tip: In sandboxed environments (like a-Shell), set environment variable:{Colors.ENDC}")
                click.echo(f"  export XMU_ROLLCALL_CONFIG_DIR=~/Documents/.xmu_rollcall")
                sys.exit(1)
        else:
            click.echo(f"{Colors.FAIL}✗ Login failed. Please check your credentials.{Colors.ENDC}")
            click.echo(f"{Colors.GRAY}Configuration not saved.{Colors.ENDC}")
            sys.exit(1)
    except Exception as e:
        click.echo(f"{Colors.FAIL}✗ Error during login validation: {str(e)}{Colors.ENDC}")
        click.echo(f"{Colors.GRAY}Configuration not saved.{Colors.ENDC}")
        sys.exit(1)

@cli.command()
def start():
    """启动签到监控"""
    # 加载配置
    config_data = load_config()

    # 检查配置是否完整
    if not is_config_complete(config_data):
        click.echo(f"{Colors.FAIL}✗ Configuration incomplete!{Colors.ENDC}")
        click.echo(f"Please run: {Colors.BOLD}XMUrollcall-cli config{Colors.ENDC}")
        sys.exit(1)

    # 启动监控
    try:
        start_monitor(config_data)
    except KeyboardInterrupt:
        click.echo(f"\n{Colors.WARNING}Shutting down...{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        click.echo(f"\n{Colors.FAIL}Error: {str(e)}{Colors.ENDC}")
        sys.exit(1)

if __name__ == '__main__':
    cli()

