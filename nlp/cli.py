"""CLI entry point for nlp."""

from __future__ import annotations

import argparse
import sys

from . import build
from . import config
from . import runner
from . import update
from . import versions

VALID_BACKENDS = {"cuda", "vulkan", "cpu"}


def _add_exec_parser(subparsers, name: str, binary_name: str) -> None:
    parser = subparsers.add_parser(name, help=f"Run {binary_name}")
    parser.add_argument("profile", help="Profile name")
    parser.add_argument("extra_args", nargs=argparse.REMAINDER, default=[])


def _parse_backends(backends_str: str | None) -> list[str] | None:
    if backends_str is None:
        return None
    backends = [b.strip() for b in backends_str.split(",")]
    for b in backends:
        if b not in VALID_BACKENDS:
            print(f"Error: Invalid backend '{b}'. Valid backends: cuda, vulkan, cpu.", file=sys.stderr)
            sys.exit(1)
    return backends


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="nlp",
        description="No Llama Cpp - CLI gateway for llama.cpp",
    )
    subparsers = parser.add_subparsers(dest="command")

    # update
    update_parser = subparsers.add_parser("update", help="Build/update to the latest llama.cpp release")
    update_parser.add_argument(
        "--backends",
        default=None,
        help="Build backends, comma-separated (cuda,vulkan,cpu). Default: auto-detect",
    )

    # install
    install_parser = subparsers.add_parser("install", help="Install a specific llama.cpp version")
    install_parser.add_argument("version", help="Version to install (e.g. b9145, 9145, or 'latest')")
    install_parser.add_argument(
        "--backends",
        default=None,
        help="Build backends, comma-separated (cuda,vulkan,cpu). Default: auto-detect",
    )

    # use
    use_parser = subparsers.add_parser("use", help="Set the active llama.cpp version")
    use_parser.add_argument("version", help="Version to use (e.g. b9145, 9145, or 'latest')")
    use_parser.add_argument(
        "--auto-install",
        action="store_true",
        help="Automatically install the version if not installed",
    )
    use_parser.add_argument(
        "--backends",
        default=None,
        help="Build backends for auto-install, comma-separated (cuda,vulkan,cpu). Default: auto-detect",
    )

    # list
    subparsers.add_parser("list", help="List installed llama.cpp versions")

    # uninstall
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall a llama.cpp version")
    uninstall_parser.add_argument("version", help="Version to uninstall (e.g. b9145 or 9145)")

    # model subcommands
    model_parser = subparsers.add_parser("model", help="Model management")
    model_sub = model_parser.add_subparsers(dest="model_command")
    model_sub.add_parser("list", help="List registered models")
    register_parser = model_sub.add_parser("register", help="Register a model")
    register_parser.add_argument("id")
    register_parser.add_argument("path")
    model_sub.add_parser("unregister", help="Unregister a model").add_argument("id")

    # profile subcommands
    profile_parser = subparsers.add_parser("profile", help="Profile management")
    profile_sub = profile_parser.add_subparsers(dest="profile_command")

    profile_sub.add_parser("list", help="List all profiles")

    create_parser = profile_sub.add_parser("create", help="Create a profile")
    create_parser.add_argument("id")
    create_parser.add_argument("--model", required=True)
    create_parser.add_argument("--system-prompt", default=None)
    create_parser.add_argument("--args", default=None)

    profile_sub.add_parser("delete", help="Delete a profile").add_argument("id")
    profile_sub.add_parser("show", help="Show a profile").add_argument("id")
    profile_sub.add_parser("edit", help="Edit config in $EDITOR")

    # core binaries
    for cmd, binary in runner.CORE_MAP.items():
        _add_exec_parser(subparsers, cmd, binary)

    # test binaries
    test_parser = subparsers.add_parser("test", help="Run test utilities")
    test_parser.add_argument("name", help="Test name (e.g. chat, grammar-parser)")
    test_parser.add_argument("profile", help="Profile name")
    test_parser.add_argument("extra_args", nargs=argparse.REMAINDER, default=[])

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Dispatch
    if args.command == "update":
        update.force_update(backends=_parse_backends(args.backends))
        return

    if args.command == "install":
        version_input = args.version
        backends = _parse_backends(args.backends)

        if version_input == "latest":
            version = update.get_latest_release_version()
            if version is None:
                print("Error: Could not determine latest release version.", file=sys.stderr)
                sys.exit(1)
            config.set_latest_version(version)
        else:
            version = versions.normalize_version(version_input)
            if not versions.is_valid_version(version):
                print(f"Error: Invalid version format '{version_input}'. Use format bXXXX or XXXX.", file=sys.stderr)
                sys.exit(1)
            if not versions.validate_release_exists(version):
                print(f"Error: Version {version} not found on GitHub. Check the version number and your network connection.", file=sys.stderr)
                sys.exit(1)

        if versions.is_version_installed(version):
            print(f"Version {version} is already installed.")
            return

        build.do_build(backends=backends, version=version)
        return

    if args.command == "use":
        version_input = args.version
        backends = _parse_backends(args.backends)

        if version_input == "latest":
            latest = config.get_latest_version()
            if latest is None:
                print("Error: No latest version set. Run 'nlp update' first.", file=sys.stderr)
                sys.exit(1)
            version = latest
        else:
            version = versions.normalize_version(version_input)
            if not versions.is_valid_version(version):
                print(f"Error: Invalid version format '{version_input}'. Use format bXXXX or XXXX.", file=sys.stderr)
                sys.exit(1)

        if not versions.is_version_installed(version):
            if args.auto_install:
                if not versions.validate_release_exists(version):
                    print(f"Error: Version {version} not found on GitHub. Check the version number and your network connection.", file=sys.stderr)
                    sys.exit(1)
                build.do_build(backends=backends, version=version)
            else:
                print(f"Error: Version {version} is not installed. Use 'nlp use {version} --auto-install' to install it.", file=sys.stderr)
                sys.exit(1)

        config.set_active_version(version)
        print(f"Now using llama.cpp {version}.")

        if version_input == "latest":
            remote_latest = update.get_latest_release_version(quiet=True)
            if remote_latest and remote_latest != version:
                print(f"Note: llama.cpp {remote_latest} is available. Run 'nlp update' to upgrade.")
        return

    if args.command == "list":
        installed = versions.list_installed_versions()
        active = config.get_active_version()
        latest = config.get_latest_version()

        if not installed:
            print("No llama.cpp versions installed.")
            return

        print("Installed llama.cpp versions:")
        for v in installed:
            markers = []
            if v == active:
                markers.append("*")
            if v == latest:
                markers.append("(latest)")
            marker_str = " ".join(markers)
            if marker_str:
                print(f"  {v} {marker_str}")
            else:
                print(f"  {v}")
        return

    if args.command == "uninstall":
        version = versions.normalize_version(args.version)
        if not versions.is_valid_version(version):
            print(f"Error: Invalid version format '{args.version}'. Use format bXXXX or XXXX.", file=sys.stderr)
            sys.exit(1)
        versions.uninstall_version(version)
        return

    if args.command == "model":
        if args.model_command == "list":
            models = config.list_models()
            if not models:
                print("No models registered.")
                return
            print("Registered models:")
            for model_id, path in sorted(models.items()):
                print(f"  {model_id}: {path}")
            return
        if args.model_command == "register":
            config.register_model(args.id, args.path)
            return
        if args.model_command == "unregister":
            config.unregister_model(args.id)
            return
        model_parser.print_help()
        sys.exit(0)

    if args.command == "profile":
        if args.profile_command == "list":
            profiles = config.list_profiles()
            if not profiles:
                print("No profiles created.")
                return
            print("Profiles:")
            for pid, p in sorted(profiles.items()):
                model_id = p.get("model", "?")
                print(f"  {pid} -> model={model_id}")
            return
        if args.profile_command == "create":
            config.create_profile(
                args.id,
                args.model,
                args.system_prompt,
                args.args,
            )
            return
        if args.profile_command == "delete":
            config.delete_profile(args.id)
            return
        if args.profile_command == "show":
            profile = config.get_profile(args.id)
            print(f"Profile: {args.id}")
            print(f"  model: {profile['model_id']} ({profile['model_path']})")
            if profile.get("system_prompt"):
                print(f"  system_prompt: {profile['system_prompt']}")
            if profile.get("args"):
                print(f"  args: {profile['args']}")
            return
        if args.profile_command == "edit":
            config.edit_config()
            return
        profile_parser.print_help()
        sys.exit(0)

    if args.command == "test":
        if args.name not in runner.TEST_NAMES:
            print(f"Error: Unknown test '{args.name}'. Run 'nlp test --help' for available tests.", file=sys.stderr)
            sys.exit(1)
        runner.run_binary(f"test-{args.name}", args.profile, args.extra_args)
        return

    # Core binaries
    if args.command in runner.CORE_MAP:
        runner.run_binary(runner.CORE_MAP[args.command], args.profile, args.extra_args)
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()