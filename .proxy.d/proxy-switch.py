#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
import re
import urllib.request
from urllib.error import URLError, HTTPError
from collections import OrderedDict
from functools import partial

PROXY_DIR = os.path.expanduser("~/.proxy.d")


def list_proxy_files(proxy_dir):
    if not os.path.isdir(proxy_dir):
        return {}

    files = []
    for fn in os.listdir(proxy_dir):
        if fn.startswith(".") or fn.endswith(".py") or fn.endswith(".sh"):
            continue
        if not os.path.isfile(os.path.join(proxy_dir, fn)):
            continue
        files.append(fn)
    names = []
    for fn in files:
        num, name = parse_proxy_name(fn)
        if name:
            names.append(((num, name), fn))
    names = sorted(names)
    result = OrderedDict()
    for (num, name), fn in names:
        if name in result:
            continue
        result[name] = os.path.join(proxy_dir, fn)
    return result


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


def echo_proxy_files(proxy_files):
    echo_log("Available proxy configurations:")
    for name, file in proxy_files.items():
        echo_log("    {} ( {} )".format(name, file))


def color_text(text, color_code):
    if color_code == "error":
        color_code = 31
    elif color_code == "info":
        color_code = 32
    elif color_code == "warning":
        color_code = 34
    return "\033[{}m{}\033[0m".format(color_code, text)


def echo_env(msg):
    print(msg, file=sys.stdout)


def echo_log(msg, color_code=None):
    if color_code is not None:
        msg = color_text(msg, color_code)
    print(msg, file=sys.stderr)


def exit_all(msg=None, exit_code=1, color_code=None):
    if msg:
        echo_log(msg, color_code=color_code)
    sys.exit(exit_code)


def check_connectivity(target_url="https://www.google.com", timeout=30):
    """
    Independent function to test network connectivity through the current proxy.
    Returns a tuple: (bool_success, status_message_or_code)
    """
    echo_log("Testing network connectivity...")

    # Configure urllib to automatically pick up the terminal's proxy environment variables
    proxy_handler = urllib.request.ProxyHandler()
    opener = urllib.request.build_opener(proxy_handler)

    # Use a realistic User-Agent to prevent getting immediately dropped by anti-bot rules
    req = urllib.request.Request(
        target_url,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
    )

    try:
        with opener.open(req, timeout=timeout) as response:
            if response.status in [200, 301, 302]:
                return True, response.status
            else:
                return False, "Unexpected Status Code ({})".format(response.status)
    except (URLError, HTTPError) as e:
        return False, "Connection Failed/Timeout"


def main():
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("-d", "--proxy-dir", default=PROXY_DIR)
    args, _ = pre_parser.parse_known_args()
    proxy_dir = args.proxy_dir
    if not proxy_dir:
        proxy_dir = PROXY_DIR

    parser = argparse.ArgumentParser(
        description="A robust terminal proxy switcher.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    # Global option to change the directory
    parser.add_argument(
        "-d",
        "--proxy-dir",
        default=proxy_dir,
        help="Path to the proxy configurations directory (default: {})".format(
            proxy_dir
        ),
    )
    proxy_dir = os.path.abspath(os.path.expanduser(proxy_dir))
    proxy_files = list_proxy_files(proxy_dir)
    proxy_name_lines = []
    for name, file in proxy_files.items():
        proxy_name_lines.append("             {}\n".format(name))
    proxy_name_lines = "".join(proxy_name_lines)
    # Positional argument for the action or proxy name
    parser.add_argument(
        "action",
        nargs="?",
        help="Options:\n"
        "  on       - Automatically switch to the first sorted proxy\n"
        "  off      - Disable all terminal proxies\n"
        "  status   - Check current proxy status and test connectivity\n"
        "  [name]   - Provide a specific proxy name to switch to it directly, choices in:\n{}".format(
            proxy_name_lines
        ),
    )
    parser.print_help = partial(parser.print_help, file=sys.stderr)
    if not os.path.isdir(proxy_dir):
        exit_all("[!] Directory {} not found.".format(proxy_dir), color_code="error")
    elif not proxy_files:
        exit_all(
            "[!] No proxy files found in {}.".format(proxy_dir), color_code="error"
        )

    args = parser.parse_args()

    if not args.action:
        echo_log(
            "[!] Missing action. Usage: proxy-switch.py {name|on|off|status}",
            color_code="warning",
        )
        echo_proxy_files(proxy_files)
        return

    target = args.action
    target = target.strip()
    proxy_envs = [
        "http_proxy",
        "https_proxy",
        "ftp_proxy",
        "rsyn_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "FTP_PROXY",
        "RSYN_PROXY",
    ]
    proxy_nos = ["no_proxy", "NO_PROXY"]

    if target == "off":
        unset_line = " ".join(proxy_envs + proxy_nos)
        echo_env("unset {};".format(unset_line))
        msg = color_text("[✗] Terminal proxy disabled.", color_code="info")
        msg = "echo '{}'".format(msg)
        echo_env(msg)
        return
    elif target == "status":
        proxy = os.environ.get("http_proxy")
        if not proxy:
            msg = color_text("Disabled", color_code="info")
            echo_log("Proxy Status: {}".format(msg))
        else:
            msg = color_text("Enabled", color_code="info")
            echo_log("Proxy Status: {} -> {}".format(msg, proxy))

            # Calling our isolated connectivity function
            success, details = check_connectivity()
            if success:
                msg = color_text("Successfully connected to Google", color_code="info")
            else:
                msg = color_text("Failed ({})".format(details), color_code="error")
            echo_log("Connectivity: {}".format(msg))
        return
    elif target == "on":
        if not proxy_files:
            exit_all("[!] No proxy configuration files found.", color_code="error")
            return
        target = list(proxy_files.keys())[0]
        msg = "[*] Automatically selecting the first proxy: {}".format(target)
        echo_log(msg, color_code="warning")
    elif target not in proxy_files:
        echo_log("[!] Proxy not found: {}".format(target), color_code="error")
        echo_proxy_files(proxy_files)
        exit_all()
        return

    proxy_file = proxy_files[target]
    with open(proxy_file, "rt") as file:
        proxy_url = file.read().strip()
    if not proxy_url:
        exit_all(
            "[!] Error: proxy file for `{}` is empty!".format(target),
            color_code="error",
        )
        return
    env_lines = ["export {}='{}';".format(proxy_envs[0], proxy_url)]
    for name in proxy_envs[1:]:
        env_lines.append("export %s=${%s};" % (name, proxy_envs[0]))
    proxy_no_url = "localhost,127.0.0.1,::1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,192.168.127.0/24,*.local,*.internal"
    env_lines.append("export {}='{}';".format(proxy_nos[0], proxy_no_url))
    for name in proxy_nos[1:]:
        env_lines.append("export %s=${%s};" % (name, proxy_nos[0]))
    echo_env("".join(env_lines))
    msg = color_text(
        "[✓] Proxy successfully switched to [{}]: {}".format(target, proxy_url),
        color_code="info",
    )
    msg = "echo '{}'".format(msg)
    echo_env(msg)


if __name__ == "__main__":
    main()
