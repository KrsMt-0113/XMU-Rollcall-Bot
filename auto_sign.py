"""Convenience script to start the XMU rollcall monitor without using the CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_local_package_on_path() -> None:
	"""Allow running from repo root without installing the package."""
	repo_dir = Path(__file__).resolve().parent
	package_dir = repo_dir / "xmu-rollcall-cli"
	if package_dir.exists():
		sys.path.insert(0, str(package_dir))


try:
	from xmu_rollcall.config import (
		get_account_by_id,
		get_all_accounts,
		get_current_account,
		get_env_account,
		is_config_complete,
		load_config,
		save_config,
		set_current_account,
	)
	from xmu_rollcall import monitor as monitor_module
except ModuleNotFoundError:
	_ensure_local_package_on_path()
	from xmu_rollcall.config import (
		get_account_by_id,
		get_all_accounts,
		get_current_account,
		get_env_account,
		is_config_complete,
		load_config,
		save_config,
		set_current_account,
	)
	from xmu_rollcall import monitor as monitor_module


def _mask_username(username: str) -> str:
	return username if len(username) <= 4 else f"{username[:2]}***{username[-2:]}"


def _print_accounts(accounts: list[dict]) -> None:
	if not accounts:
		print("No accounts configured. Run `xmu-rollcall-cli account add` first.")
		return
	for account in accounts:
		aid = account.get("id")
		label = account.get("name") or account.get("username") or "<unnamed>"
		username = account.get("username", "")
		source = " [环境变量]" if account.get("from_env") else ""
		print(f"[{aid}] {label}{source} ({_mask_username(username)})")


def _pick_account(config: dict, account_id: int | None) -> dict | None:
	if account_id is not None:
		return get_account_by_id(config, account_id)
	return get_current_account(config)


def main() -> None:
	parser = argparse.ArgumentParser(description="Run XMU rollcall auto sign monitor.")
	parser.add_argument("--account-id", type=int, help="Account ID from config to use.")
	parser.add_argument("--list", action="store_true", help="List configured accounts and exit.")
	parser.add_argument(
		"--set-default",
		action="store_true",
		help="Persist the provided account id as the new default.",
	)
	parser.add_argument(
		"--interval",
		type=int,
		default=30,
		help="Polling interval in seconds (default: 30).",
	)
	args = parser.parse_args()

	config = load_config()
	accounts = list(get_all_accounts(config))
	env_account = get_env_account()
	if env_account:
		accounts.append(env_account)

	if args.list:
		_print_accounts(accounts)
		return

	# if not accounts:
	# 	print("No accounts configured. Use the CLI to add credentials first.")
	# 	sys.exit(1)

	account = _pick_account(config, args.account_id)
	if account is None:
		print("Unable to find the requested account. Run with --list to see IDs.")
		sys.exit(1)

	if args.account_id is not None and args.set_default:
		set_current_account(config, account["id"])
		save_config(config)

	if not is_config_complete({"current_account_id": account.get("id"), "accounts": [account]}):
		print("Selected account is missing username/password.")
		sys.exit(1)

	print(f"Starting monitor with account [{account['id']}] {account.get('name') or account['username']}")
	monitor_module.interval = max(1, args.interval)
	monitor_module.start_monitor(account)


if __name__ == "__main__":
	main()
