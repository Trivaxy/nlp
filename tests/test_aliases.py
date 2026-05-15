from __future__ import annotations

import os
from pathlib import Path

from nlp.runner import CORE_MAP, TEST_NAMES
from nlp.versions import list_installed_versions, get_version_dir


def _get_any_version_dir() -> Path | None:
    versions = list_installed_versions()
    if not versions:
        return None
    version_dir = get_version_dir(versions[0])
    if not version_dir.exists() or not any(version_dir.iterdir()):
        return None
    return version_dir


def test_core_binaries_exist():
    version_dir = _get_any_version_dir()
    if version_dir is None:
        return
    missing = []
    for cmd, binary in CORE_MAP.items():
        path = version_dir / binary
        if not path.exists():
            missing.append(f"{cmd} -> {binary}")
    assert not missing, f"Missing core binaries:\n" + "\n".join(missing)


def test_core_binaries_executable():
    version_dir = _get_any_version_dir()
    if version_dir is None:
        return
    non_exec = []
    for cmd, binary in CORE_MAP.items():
        path = version_dir / binary
        if path.exists() and not os.access(path, os.X_OK):
            non_exec.append(f"{cmd} -> {binary}")
    assert not non_exec, f"Non-executable binaries:\n" + "\n".join(non_exec)


def test_test_binaries_exist():
    version_dir = _get_any_version_dir()
    if version_dir is None:
        return
    missing = []
    for name in TEST_NAMES:
        path = version_dir / f"test-{name}"
        if not path.exists():
            missing.append(f"test-{name}")
    assert not missing, f"Missing test binaries:\n" + "\n".join(missing)