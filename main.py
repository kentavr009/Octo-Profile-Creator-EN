#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch create Octo Browser profiles.

• Read proxy settings from proxies.csv
• Load optional cookies from cookies.json
• Octo automatically generates a fingerprint using the default template
• Number of profiles is defined by PROFILE_COUNT (default = number of proxies)
"""

import csv
import json
import os
import sys
import time
import itertools
from pathlib import Path
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

# ───────────────────────── CONFIG ──────────────────────────
API_BASE = "https://app.octobrowser.net/api/v2/automation"
REQ_TIMEOUT = 30  # seconds
DEFAULT_FP = {"os": "win", "screen": "1920x1080"}

BASE_DIR = Path(__file__).parent.resolve()
load_dotenv()  # load environment variables from .env file

TOKEN = os.getenv("OCTO_API_TOKEN", "")
if not TOKEN:
    sys.exit("🛑 Specify OCTO_API_TOKEN in .env")

HEADERS = {"X-Octo-Api-Token": TOKEN}

PROXY_CSV = BASE_DIR / os.getenv("PROXY_FILE", "proxies.csv")
COOKIE_JSON = BASE_DIR / os.getenv("COOKIE_FILE", "cookies.json")
PROFILE_COUNT = int(os.getenv("PROFILE_COUNT", "0"))  # 0 -> use len(proxies)

# ──────────────────────── UTILITIES ────────────────────────
def sniff(path: Path) -> csv.Dialect:
    """
    Detect CSV dialect by sampling the file.
    """
    sample = path.read_text(encoding="utf-8")[:1024]
    return csv.Sniffer().sniff(sample, delimiters=",;\t ")


def load_proxies(path: Path) -> List[Dict[str, Any]]:
    """
    Load proxy configurations from a CSV file.
    """
    if not path.exists():
        sys.exit(f"🛑 Proxies file not found: {path}")

    dialect = sniff(path)
    proxies: List[Dict[str, Any]] = []

    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, dialect=dialect)
        for row in reader:
            p = {k.strip(): v.strip() for k, v in row.items() if v and k}
            try:
                # Octo API expects port as a string; converting to str validates it's numeric
                p["port"] = str(p["port"])
            except Exception:
                sys.exit(f"🛑 Invalid proxy row: {row}")
            proxies.append(p)

    if not proxies:
        sys.exit("🛑 No proxies loaded")

    return proxies


def load_cookies(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load cookies mapping from a JSON file.
    """
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        sys.exit("🛑 cookies.json must be a JSON object")

    return data


def api_post(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper to send POST requests to the Octo API and return the 'data' field.
    """
    url = f"{API_BASE}/{endpoint.lstrip('/')}"
    resp = requests.post(url, json=payload, headers=HEADERS, timeout=REQ_TIMEOUT)
    resp.raise_for_status()
    check_limits(resp)  # implement dynamic pause based on rate limits
    return resp.json()["data"]


def check_limits(response: requests.Response) -> None:
    """
    Analyze X-RateLimit headers and pause if necessary.

    • rpm  (X-RateLimit-Remaining)      — remaining requests per minute
    • rph  (X-RateLimit-Remaining-Hour) — remaining requests per hour
    If rpm < 10, sleep for 60s; if rph < 10, sleep for 3600s.
    """
    rpm = int(response.headers.get("x-ratelimit-remaining", 0))
    rph = int(response.headers.get("x-ratelimit-remaining-hour", 0))
    print(f"RPM remaining: {rpm} | RPH remaining: {rph}")

    if rpm < 10:
        print("⚠ Approaching RPM limit, sleeping for 1 minute...")
        time.sleep(60)
    if rph < 10:
        print("⚠ Approaching RPH limit, sleeping for 1 hour...")
        time.sleep(3600)


# ─────────────────────────── MAIN ──────────────────────────
def main() -> None:
    proxies = load_proxies(PROXY_CSV)
    cookies_map = load_cookies(COOKIE_JSON)

    # determine how many profiles to create
    total = PROFILE_COUNT if PROFILE_COUNT > 0 else len(proxies)
    proxy_cycle = itertools.cycle(proxies)

    for idx in range(1, total + 1):
        proxy = next(proxy_cycle)
        title = f"BatchProfile_{idx}"
        cookies = cookies_map.get(str(idx - 1))

        payload: Dict[str, Any] = {
            "title": title,
            "proxy": proxy,
            "fingerprint": DEFAULT_FP,
        }
        if cookies:
            payload["cookies"] = cookies

        try:
            data = api_post("profiles", payload)
            print(f"✅ Profile #{idx} created → UUID {data['uuid']}")
        except requests.HTTPError as e:
            print(f"❌ HTTP error for profile #{idx}: {e}")
            print("   Server response:", e.response.text)


# ────────────────────────── ENTRYPOINT ─────────────────────
if __name__ == "__main__":
    main()
