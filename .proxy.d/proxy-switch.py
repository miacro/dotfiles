#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
import re

PROXY_DIR = os.path.expanduser("~/.proxy.d")


def get_proxy_files(proxy_dir):
    if not os.path.isdir(proxy_dir):
        exit_all("echo '\033[31m[!] Directory {} not found.\033[0m'".format(proxy_dir))
        return

    # Filter out hidden files and the script itself if it lives in the same directory
    files = []
    for fn in os.listdir(proxy_dir):
        if fn.startswith(".") or fn.endswith(".py") or fn.endswith(".sh"):
            continue
        if not os.path.isfile(os.path.join(proxy_dir, fn)):
            continue
        files.append(fn)
    # Sort files numerically by the prefix before the '-'
    files.sort(
        key=lambda x: (
            int(x.split("-")[0]) if x.split("-")[0].isdigit() else float("inf")
        )
    )
    return files


def get_proxy_name(proxy_file):
    proxy_name = os.path.basename(proxy_file)
    idx = proxy_name.find("-")
    if idx >= 0:
        proxy_name = proxy_name[idx + 1 :]
    return proxy_name


def parse_proxy_name(proxy_file):
    pattern = r"^([0-9]+)-?"
    proxy_name = os.path.basename(proxy_file)
    matched = re.search(pattern, proxy_name)
    if not matched:
        return 0, proxy_name
    proxy_num = int(matched.group(1))
    head, tail = matched.span()
    proxy_name = proxy_name[tail:]
    return proxy_num, proxy_name


def print_available(files):
    print(
        "echo 'Available proxy configurations (Sorted numerically):'", file=sys.stderr
    )
    for f in files:
        print(f"echo '  - {get_clean_name(f)}'", file=sys.stderr)


def echo_env(msg):
    print(msg, file=sys.stdout)


def echo_log(msg):
    print(msg, file=sys.stderr)


def exit_all(msg=None, code=1):
    if msg:
        echo_log(msg)
    sys.exit(code)


def main():
    parser = argparse.ArgumentParser(
        description="A robust terminal proxy switcher.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Global option to change the directory
    parser.add_argument(
        "-d",
        "--proxy-dir",
        default=PROXY_DIR,
        help="Path to the proxy configurations directory (default: {})".format(
            PROXY_DIR
        ),
    )

    # Positional argument for the action or proxy name
    parser.add_argument(
        "action",
        nargs="?",
        help="Options:\n"
        "  on       - Automatically switch to the first sorted proxy\n"
        "  off      - Disable all terminal proxies\n"
        "  status   - Check current proxy status and test connectivity\n"
        "  [name]   - Provide a specific proxy name to switch to it directly",
    )

    args = parser.parse_args()
    proxy_dir = os.path.abspath(os.path.expanduser(args.proxy_dir))

    # If no action is provided, print usage and available configurations
    if not args.action:
        files = get_proxy_files(proxy_dir)
        echo_log(
            "echo '\033[31m[!] Missing argument. Usage: setproxy {name|on|off|status}\033[0m'",
        )
        print_available(files)
        return

    target = args.action
    files = get_proxy_files(proxy_dir)

    # 1. Action: OFF
    if target == "off":
        print(
            "unset http_proxy https_proxy ftp_proxy rsyn_proxy HTTP_PROXY HTTPS_PROXY FTP_PROXY RSYN_PROXY;"
        )
        print("echo '\033[31m[✗] Terminal proxy disabled.\033[0m'")
        return

    # 2. Action: STATUS
    if target == "status":
        current_proxy = os.environ.get("http_proxy")
        if not current_proxy:
            print("echo 'Proxy Status: \033[31mDisabled\033[0m'")
        else:
            print(f"echo 'Proxy Status: \033[32mEnabled\033[0m -> {current_proxy}'")
            print("echo 'Testing network connectivity...'")
            try:
                subprocess.run(
                    ["curl", "-I", "--connect-timeout", "3", "https://www.google.com"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
                print(
                    "echo 'Connectivity: \033[32mSuccessfully connected to Google\033[0m'"
                )
            except subprocess.CalledProcessError:
                print("echo 'Connectivity: \033[31mFailed to connect to Google\033[0m'")
        return

    # 3. Action: ON (Auto-select first)
    if target == "on":
        if not files:
            print(
                "echo '\033[31m[!] No proxy configuration files found.\033[0m'",
                file=sys.stderr,
            )
            sys.exit(1)
        target = get_clean_name(files[0])
        print(
            "echo '\033[34m[*] Automatically selecting the first proxy in order...\033[0m'"
        )

    # 4. Action: Switch to a custom named proxy
    matched_file = None
    for f in files:
        if get_clean_name(f) == target:
            matched_file = f
            break

    if matched_file:
        config_path = os.path.join(proxy_dir, matched_file)
        with open(config_path, "r") as file:
            proxy_url = file.read().strip()

        if not proxy_url:
            print(
                f"echo '\033[31m[!] Error: Configuration file for `{target}` is empty!\033[0m'",
                file=sys.stderr,
            )
            sys.exit(1)

        # Output shell commands for execution
        print(
            f"export http_proxy='{proxy_url}' https_proxy='{proxy_url}' ftp_proxy='{proxy_url}' rsyn_proxy='{proxy_url}';"
        )
        print(f"export HTTP_PROXY='{proxy_url}' HTTPS_PROXY='{proxy_url}';")
        print(
            "export no_proxy='localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12';"
        )
        print(
            "export NO_PROXY='localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12';"
        )
        print(
            f"echo '\033[32m[✓] Proxy successfully switched to [{target}]: {proxy_url}\033[0m'"
        )
    else:
        print(
            f"echo '\033[31m[!] Proxy configuration not found: {target}\033[0m'",
            file=sys.stderr,
        )
        print_available(files)
        sys.exit(1)


if __name__ == "__main__":
    main()
