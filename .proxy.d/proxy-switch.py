#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
import re
import shlex
import urllib.request
from http.client import HTTPException, InvalidURL
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit

PROXY_DIR = os.path.expanduser("~/.proxy.d")


def list_proxy_files(proxy_dir):
    if not os.path.isdir(proxy_dir):
        return []

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
    return [(name, os.path.join(proxy_dir, fn)) for (num, name), fn in names]


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


def format_proxy_files(proxy_files):
    lines = []
    seen = set()
    home = os.path.expanduser("~")
    home_prefix = os.path.join(home, "")
    for index, (name, file) in enumerate(proxy_files, start=1):
        shadowed = name in seen
        seen.add(name)
        suffix = " [shadowed]" if shadowed else ""
        try:
            proxy = redact_proxy_url(read_proxy_url(file))
        except ValueError as error:
            proxy = "<{}>".format(error)
        display_file = file
        if file == home:
            display_file = "~"
        elif file.startswith(home_prefix):
            display_file = "~/" + file[len(home_prefix):]
        line = "    {}. {} ( {} ) -> {}{}".format(index, name, display_file, proxy, suffix)
        lines.append(color_text(line, "gray" if shadowed else "info"))
    return lines


def echo_proxy_files(proxy_files):
    echo_log("Available proxy configurations (gray entries are selectable by index):")
    for line in format_proxy_files(proxy_files):
        echo_log(line)


def color_text(text, color_code):
    if color_code == "error":
        color_code = 31
    elif color_code == "info":
        color_code = 32
    elif color_code == "warning":
        color_code = 34
    elif color_code == "gray":
        color_code = 90
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


def read_proxy_url(proxy_file):
    proxy_url = ""
    try:
        with open(proxy_file, "rt", encoding="utf-8") as file:
            for line in file:
                proxy_url = line.partition("#")[0].strip()
                if proxy_url:
                    break
    except OSError as error:
        raise ValueError("Unable to read proxy file {}: {}".format(proxy_file, error)) from None
    except UnicodeError:
        raise ValueError("Proxy file {} is not valid UTF-8 text.".format(proxy_file)) from None
    if not proxy_url:
        raise ValueError("Proxy file {} contains no proxy URL!".format(proxy_file))
    try:
        parse_proxy_url(proxy_url)
    except ValueError as error:
        raise ValueError("Invalid proxy URL in {}: {}".format(proxy_file, error)) from None
    return proxy_url


def parse_proxy_url(proxy_url):
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in proxy_url):
        raise ValueError("whitespace and control characters must be percent-encoded")
    added_slashes = "://" not in proxy_url and not proxy_url.startswith("//")
    try:
        parsed = urlsplit("//" + proxy_url if added_slashes else proxy_url)
    except ValueError:
        raise ValueError("malformed proxy URL or host") from None
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError(
            "proxy URL must not contain a path, query or fragment; "
            "percent-encode reserved characters in credentials"
        )
    if not parsed.hostname:
        raise ValueError("proxy host is missing")
    try:
        port = parsed.port
    except ValueError:
        raise ValueError("proxy port must be a number from 1 to 65535") from None
    if port == 0 or parsed.netloc.rpartition("@")[2].endswith(":"):
        raise ValueError("proxy port must be a number from 1 to 65535")
    return parsed


def redact_proxy_url(proxy_url):
    try:
        parsed = parse_proxy_url(proxy_url)
    except ValueError:
        return "<invalid proxy URL>"
    userinfo, at, host = parsed.netloc.rpartition("@")
    username, colon, _ = userinfo.partition(":")
    if not at or not colon:
        return proxy_url
    redacted = parsed._replace(netloc="{}:***@{}".format(username, host)).geturl()
    added_slashes = "://" not in proxy_url and not proxy_url.startswith("//")
    return redacted[2:] if added_slashes else redacted


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # A redirected request could use a different proxy or bypass it entirely.
        return None


def check_connectivity(target_url="https://www.google.com", timeout=30):
    """
    Independent function to test network connectivity through the current proxy.
    Returns (True/False/None, details); None means the proxy was not tested.
    """
    try:
        target = urlsplit(target_url)
        if target.scheme not in ("http", "https"):
            return None, "Connectivity checks support only HTTP and HTTPS targets"
        if not target.hostname:
            return False, "Invalid proxy or target URL"

        proxy_settings = urllib.request.getproxies()
        proxy_url = proxy_settings.get(target.scheme) or proxy_settings.get("all")
        if not proxy_url:
            return None, "No {} proxy configured ({}_proxy or all_proxy)".format(
                target.scheme.upper(), target.scheme
            )
        proxy = parse_proxy_url(proxy_url)
        proxy_scheme = proxy.scheme or "http"
        if proxy_scheme != "http":
            return (
                None,
                "Built-in connectivity check does not support {} proxies".format(
                    proxy_scheme.upper()
                ),
            )

        req = urllib.request.Request(
            target_url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            },
        )
        if urllib.request.proxy_bypass(req.host):
            return None, "Target bypasses the proxy due to no_proxy or system settings"

        proxy_handler = urllib.request.ProxyHandler(
            {target.scheme: proxy._replace(scheme="http").geturl()}
        )
        opener = urllib.request.build_opener(proxy_handler, NoRedirectHandler())
        echo_log(
            "Testing {} connectivity via {}...".format(
                target.scheme.upper(), redact_proxy_url(proxy_url)
            )
        )
        with opener.open(req, timeout=timeout) as response:
            if response.status in [200, 301, 302]:
                return True, response.status
            else:
                return False, "Unexpected Status Code ({})".format(response.status)
    except (InvalidURL, ValueError):
        return False, "Invalid proxy or target URL"
    except HTTPError as error:
        if error.code in (301, 302, 303, 307, 308):
            return True, error.code
        return False, "Unexpected Status Code ({})".format(error.code)
    except (URLError, OSError, HTTPException):
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
            proxy_dir.replace("%", "%%")
        ),
    )
    proxy_dir = os.path.abspath(os.path.expanduser(proxy_dir))
    proxy_files_error = None
    try:
        proxy_files = list_proxy_files(proxy_dir)
    except OSError as error:
        proxy_files = []
        proxy_files_error = error
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--name",
        dest="proxy_name",
        metavar="NAME",
        help="Select the highest-priority configuration for an exact name, including numeric names or reserved commands",
    )
    # Positional argument for the action, index, or proxy name
    selection.add_argument(
        "action",
        nargs="?",
        help="Options:\n"
        "  on       - Automatically switch to the first sorted proxy\n"
        "  off      - Disable all terminal proxies\n"
        "  status   - Check current proxy status and test connectivity\n"
        "  [index]  - Select any proxy by its 1-based index, including gray entries\n"
        "  [name]   - Select the highest-priority configuration for this name\n"
        "Green entries are selected by name; gray entries are shadowed.",
    )
    original_print_help = parser.print_help

    def print_proxy_help(file=None):
        if file is None:
            file = sys.stderr
        original_print_help(file=file)
        if proxy_files:
            print("\nAvailable proxy configurations:", file=file)
            for line in format_proxy_files(proxy_files):
                print(line, file=file)

    parser.print_help = print_proxy_help
    args = parser.parse_args()

    target = (args.action or "").strip()
    needs_config = args.proxy_name is not None or target not in ("off", "status")
    if needs_config:
        if proxy_files_error is not None:
            exit_all(
                "[!] Unable to read proxy configurations from {}: {}".format(
                    proxy_dir, proxy_files_error
                ),
                color_code="error",
            )
        if not os.path.isdir(proxy_dir):
            exit_all(
                "[!] Directory {} not found.".format(proxy_dir), color_code="error"
            )
        elif not proxy_files:
            exit_all(
                "[!] No proxy files found in {}.".format(proxy_dir), color_code="error"
            )

    if not args.action and args.proxy_name is None:
        echo_log(
            "[!] Missing action. Usage: proxy-switch.py {index|name|on|off|status} or --name NAME",
            color_code="warning",
        )
        echo_proxy_files(proxy_files)
        return

    proxy_envs = [
        "http_proxy",
        "https_proxy",
        "ftp_proxy",
        "rsync_proxy",
        "all_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "FTP_PROXY",
        "RSYNC_PROXY",
        "ALL_PROXY",
    ]
    proxy_nos = ["no_proxy", "NO_PROXY"]

    proxy_file = None
    if args.proxy_name is not None:
        target = args.proxy_name
    elif target == "off":
        unset_line = " ".join(proxy_envs + proxy_nos)
        echo_env("unset {};".format(unset_line))
        msg = color_text("[✗] Terminal proxy disabled.", color_code="info")
        msg = "printf '%s\\n' {}".format(shlex.quote(msg))
        echo_env(msg)
        return
    elif target == "status":
        proxy_settings = urllib.request.getproxies()
        active_proxies = [
            (scheme, proxy_settings[scheme])
            for scheme in ("http", "https", "ftp", "rsync", "all")
            if proxy_settings.get(scheme)
        ]
        if not active_proxies:
            msg = color_text("Disabled", color_code="info")
            echo_log("Proxy Status: {}".format(msg))
        else:
            msg = color_text("Enabled", color_code="info")
            echo_log("Proxy Status: {}".format(msg))
            for scheme, proxy in active_proxies:
                echo_log("    {}_proxy -> {}".format(scheme, redact_proxy_url(proxy)))

            # Calling our isolated connectivity function
            success, details = check_connectivity()
            if success is None:
                msg = color_text(
                    "Not tested ({})".format(details), color_code="warning"
                )
            elif success:
                msg = color_text(
                    "Successfully connected to Google through the configured proxy",
                    color_code="info",
                )
            else:
                msg = color_text("Failed ({})".format(details), color_code="error")
            echo_log("Connectivity: {}".format(msg))
        return

    elif target == "on":
        target, proxy_file = proxy_files[0]
        msg = "[*] Automatically selecting the first proxy: {}".format(target)
        echo_log(msg, color_code="warning")
    elif target.isdecimal():
        try:
            index = int(target)
        except ValueError:
            # Python may reject decimal strings exceeding its integer digit limit.
            index = 0
        if not 1 <= index <= len(proxy_files):
            echo_log(
                "[!] Proxy index out of range: {}".format(target), color_code="error"
            )
            echo_proxy_files(proxy_files)
            exit_all()
        target, proxy_file = proxy_files[index - 1]
    if proxy_file is None:
        proxy_file = next((file for name, file in proxy_files if name == target), None)
    if proxy_file is None:
        echo_log("[!] Proxy not found: {}".format(target), color_code="error")
        echo_proxy_files(proxy_files)
        exit_all()
        return

    try:
        proxy_url = read_proxy_url(proxy_file)
    except ValueError as error:
        exit_all("[!] {}".format(error), color_code="error")
    env_lines = ["export {}={};".format(proxy_envs[0], shlex.quote(proxy_url))]
    for name in proxy_envs[1:]:
        env_lines.append('export %s="${%s}";' % (name, proxy_envs[0]))
    proxy_no_url = "localhost,127.0.0.1,::1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,192.168.127.0/24,*.local,*.internal"
    env_lines.append("export {}={};".format(proxy_nos[0], shlex.quote(proxy_no_url)))
    for name in proxy_nos[1:]:
        env_lines.append('export %s="${%s}";' % (name, proxy_nos[0]))
    echo_env("".join(env_lines))
    msg = color_text(
        "[✓] Proxy successfully switched to [{}]: {}".format(
            target, redact_proxy_url(proxy_url)
        ),
        color_code="info",
    )
    msg = "printf '%s\\n' {}".format(shlex.quote(msg))
    echo_env(msg)


if __name__ == "__main__":
    main()
