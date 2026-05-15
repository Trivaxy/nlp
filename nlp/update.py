"""Update checking and prompting for nlp."""

from __future__ import annotations

import re
import sys

import requests
from bs4 import BeautifulSoup

from .build import do_build
from .config import set_latest_version
from .versions import is_version_installed

LLAMA_RELEASES_URL = "https://github.com/ggml-org/llama.cpp/releases"


def get_latest_release_version(*, quiet: bool = False) -> str | None:
    """Fetch the latest llama.cpp release tag from GitHub releases page."""
    if not quiet:
        print("Checking for latest llama.cpp release...")
    try:
        resp = requests.get(LLAMA_RELEASES_URL, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        if not quiet:
            print(f"Error fetching releases page: {e}", file=sys.stderr)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    tag = soup.find("a", class_="Link", href=re.compile(r"/tag/"))
    if tag and tag.get("href"):
        href = tag["href"]
        match = re.search(r"/tag/(b\d+)", href)
        if match:
            return match.group(1)

    tags = soup.find_all("a", href=re.compile(r"/ggml-org/llama\.cpp/releases/tag/"))
    for t in tags:
        href = t.get("href", "")
        match = re.search(r"/tag/(b\d+)", href)
        if match:
            return match.group(1)

    if not quiet:
        print("Could not parse latest version from GitHub.")
    return None


def force_update(*, backends: list[str] | None = None) -> None:
    """Force an update to the latest version."""
    latest = get_latest_release_version()
    if latest is None:
        print("Error: Could not determine latest release version.", file=sys.stderr)
        sys.exit(1)

    if is_version_installed(latest):
        print(f"Version {latest} is already installed.")
        set_latest_version(latest)
        print(f"Run 'nlp use {latest}' to activate.")
        return

    do_build(backends=backends, version=latest)
    set_latest_version(latest)
    print(f"Run 'nlp use {latest}' to activate.")