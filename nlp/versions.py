"""Version management for llama.cpp installations."""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import requests

VERSIONS_DIR = Path(__file__).parent / "llama-bin"
VERSION_RE = re.compile(r"^b(\d+)$")
LLAMA_REPO = "https://github.com/ggml-org/llama.cpp"


def normalize_version(v: str) -> str:
    if v == "latest":
        return v
    if v.isdigit():
        return f"b{v}"
    return v


def is_valid_version(v: str) -> bool:
    v = normalize_version(v)
    return bool(VERSION_RE.match(v))


def is_version_installed(v: str) -> bool:
    return get_version_dir(v).exists()


def list_installed_versions() -> list[str]:
    if not VERSIONS_DIR.exists():
        return []
    versions = []
    for item in VERSIONS_DIR.iterdir():
        if item.is_dir() and VERSION_RE.match(item.name):
            versions.append(item.name)
    versions.sort(key=_build_number)
    return versions


def get_version_dir(v: str) -> Path:
    v = normalize_version(v)
    return VERSIONS_DIR / v


def validate_release_exists(v: str) -> bool:
    v = normalize_version(v)
    url = f"{LLAMA_REPO}/releases/tag/{v}"
    try:
        resp = requests.head(url, timeout=15, allow_redirects=True)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def uninstall_version(v: str) -> None:
    from .config import get_active_version, get_latest_version, set_active_version, set_latest_version

    v = normalize_version(v)
    version_dir = get_version_dir(v)
    if not version_dir.exists():
        print(f"Error: Version {v} is not installed.", file=sys.stderr)
        sys.exit(1)

    shutil.rmtree(version_dir)
    print(f"Uninstalled llama.cpp {v}.")

    active = get_active_version()
    if v == active:
        set_active_version(None)
        print("Warning: The active version was uninstalled. Run 'nlp use <version>' to set a new active version.")

    latest = get_latest_version()
    if v == latest:
        set_latest_version(None)


def _build_number(version: str) -> int:
    match = VERSION_RE.match(version)
    return int(match.group(1)) if match else 0