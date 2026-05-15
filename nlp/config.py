"""Configuration management for nlp."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from platformdirs import user_config_dir

CONFIG_DIR = Path(os.environ.get("NLP_CONFIG_DIR", user_config_dir("nlp")))
CONFIG_FILE = CONFIG_DIR / "config.toml"


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load config from TOML file. Returns empty dict if missing."""
    if not CONFIG_FILE.exists():
        return {}
    with CONFIG_FILE.open("rb") as f:
        return tomllib.load(f)


def _dump_config(config: dict) -> str:
    """Serialize config dict to a simple TOML string."""
    lines = []

    active_version = config.get("active_version")
    latest_version = config.get("latest_version")
    if active_version is not None:
        lines.append(f'active_version = {_escape_str(active_version)}')
    if latest_version is not None:
        lines.append(f'latest_version = {_escape_str(latest_version)}')

    models = config.get("models", {})
    if models:
        if lines:
            lines.append("")
        lines.append("[models]")
        for key, value in sorted(models.items()):
            lines.append(f'"{key}" = {_escape_str(value)}')
        lines.append("")

    profiles = config.get("profiles", {})
    for profile_id, profile in sorted(profiles.items()):
        lines.append(f'[profiles.{profile_id}]')
        model = profile.get("model")
        if model is not None:
            lines.append(f'model = {_escape_str(model)}')
        system_prompt = profile.get("system_prompt")
        if system_prompt is not None:
            lines.append(f'system_prompt = {_escape_str(system_prompt)}')
        args = profile.get("args")
        if args is not None:
            lines.append(f'args = {_escape_str(args)}')
        lines.append("")

    return "\n".join(lines)


def _escape_str(value: str) -> str:
    """Escape a string for TOML."""
    value = (
        value.replace("\\", "\\\\")
        .replace("\"", "\\\"")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{value}"'


def save_config(config: dict) -> None:
    """Save config atomically to TOML file."""
    _ensure_dir()
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(_dump_config(config))
    tmp.rename(CONFIG_FILE)


def ensure_config_exists() -> dict:
    """Ensure config file exists, creating an empty one if needed. Returns config."""
    if not CONFIG_FILE.exists():
        _ensure_dir()
        CONFIG_FILE.write_text("")
    return load_config()


# Model helpers

def _validate_id(model_id: str) -> None:
    if not model_id:
        print("Error: ID cannot be empty.", file=sys.stderr)
        sys.exit(1)
    if " " in model_id:
        print("Error: ID cannot contain spaces.", file=sys.stderr)
        sys.exit(1)


def register_model(model_id: str, path: str) -> None:
    config = ensure_config_exists()
    _validate_id(model_id)
    abs_path = str(Path(path).expanduser().resolve())
    if not Path(abs_path).exists():
        print(f"Error: File not found: {abs_path}", file=sys.stderr)
        sys.exit(1)
    models = config.setdefault("models", {})
    if model_id in models:
        print(f"Error: Model '{model_id}' already registered.", file=sys.stderr)
        sys.exit(1)
    models[model_id] = abs_path
    save_config(config)
    print(f"Registered model '{model_id}' -> {abs_path}")


def unregister_model(model_id: str) -> None:
    config = load_config()
    models = config.get("models", {})
    if model_id not in models:
        print(f"Error: Model '{model_id}' not found.", file=sys.stderr)
        sys.exit(1)
    profiles = config.get("profiles", {})
    refs = [pid for pid, p in profiles.items() if p.get("model") == model_id]
    if refs:
        print(f"Error: Cannot unregister '{model_id}': referenced by profiles: {', '.join(refs)}", file=sys.stderr)
        sys.exit(1)
    del models[model_id]
    save_config(config)
    print(f"Unregistered model '{model_id}'")


def get_model(model_id: str) -> str:
    config = load_config()
    models = config.get("models", {})
    if model_id not in models:
        print(f"Error: Unknown model '{model_id}'.", file=sys.stderr)
        sys.exit(1)
    path = models[model_id]
    if not Path(path).exists():
        print(f"Error: Model file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return path


def list_models() -> dict:
    return load_config().get("models", {})


# Profile helpers

def create_profile(profile_id: str, model_id: str, system_prompt: str | None, args: str | None) -> None:
    config = ensure_config_exists()
    _validate_id(profile_id)
    models = config.get("models", {})
    if model_id not in models:
        print(f"Error: Unknown model '{model_id}'.", file=sys.stderr)
        sys.exit(1)
    profiles = config.setdefault("profiles", {})
    if profile_id in profiles:
        print(f"Error: Profile '{profile_id}' already exists.", file=sys.stderr)
        sys.exit(1)
    profile: dict[str, str] = {"model": model_id}
    if system_prompt is not None:
        profile["system_prompt"] = system_prompt
    if args is not None:
        profile["args"] = args
    profiles[profile_id] = profile
    save_config(config)
    print(f"Created profile '{profile_id}'")


def delete_profile(profile_id: str) -> None:
    config = load_config()
    profiles = config.get("profiles", {})
    if profile_id not in profiles:
        print(f"Error: Profile '{profile_id}' not found.", file=sys.stderr)
        sys.exit(1)
    del profiles[profile_id]
    save_config(config)
    print(f"Deleted profile '{profile_id}'")


def get_profile(profile_id: str) -> dict:
    config = load_config()
    profiles = config.get("profiles", {})
    if profile_id not in profiles:
        print(f"Error: Profile '{profile_id}' not found.", file=sys.stderr)
        sys.exit(1)
    profile = profiles[profile_id]
    model_id = profile.get("model")
    if model_id is None:
        print(f"Error: Profile '{profile_id}' has no model assigned.", file=sys.stderr)
        sys.exit(1)
    models = config.get("models", {})
    if model_id not in models:
        print(f"Error: Profile '{profile_id}' references unknown model '{model_id}'.", file=sys.stderr)
        sys.exit(1)
    path = models[model_id]
    if not Path(path).exists():
        print(f"Error: Model file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return {
        "model_id": model_id,
        "model_path": path,
        "system_prompt": profile.get("system_prompt"),
        "args": profile.get("args"),
    }


def list_profiles() -> dict:
    return load_config().get("profiles", {})


def edit_config() -> None:
    """Open the config file in $EDITOR."""
    ensure_config_exists()
    editor = os.environ.get("EDITOR")
    if not editor:
        for fallback in ("nano", "vi"):
            if shutil.which(fallback):
                editor = fallback
                break
    if not editor:
        print("Error: $EDITOR is not set.", file=sys.stderr)
        sys.exit(1)
    subprocess.run([editor, str(CONFIG_FILE)], check=False)


def get_active_version() -> str | None:
    """Get the currently active llama.cpp version from config."""
    config = load_config()
    return config.get("active_version")


def set_active_version(v: str | None) -> None:
    """Set the active llama.cpp version in config."""
    config = ensure_config_exists()
    if v is None:
        config.pop("active_version", None)
    else:
        config["active_version"] = v
    save_config(config)


def get_latest_version() -> str | None:
    """Get the latest llama.cpp version from config."""
    config = load_config()
    return config.get("latest_version")


def set_latest_version(v: str | None) -> None:
    """Set the latest llama.cpp version in config."""
    config = ensure_config_exists()
    if v is None:
        config.pop("latest_version", None)
    else:
        config["latest_version"] = v
    save_config(config)
