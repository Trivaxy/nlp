"""Execution layer for nlp."""

from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path

from .config import get_active_version, get_profile
from .versions import get_version_dir

CORE_MAP = {
    "cli": "llama-cli",
    "server": "llama-server",
    "quantize": "llama-quantize",
    "bench": "llama-bench",
    "embedding": "llama-embedding",
    "perplexity": "llama-perplexity",
    "tokenize": "llama-tokenize",
    "batched": "llama-batched",
    "batched-bench": "llama-batched-bench",
    "parallel": "llama-parallel",
    "speculative": "llama-speculative",
    "speculative-simple": "llama-speculative-simple",
    "lookahead": "llama-lookahead",
    "lookup": "llama-lookup",
    "lookup-create": "llama-lookup-create",
    "lookup-stats": "llama-lookup-stats",
    "passkey": "llama-passkey",
    "save-load-state": "llama-save-load-state",
    "export-lora": "llama-export-lora",
    "finetune": "llama-finetune",
    "imatrix": "llama-imatrix",
    "gguf": "llama-gguf",
    "gguf-split": "llama-gguf-split",
    "gguf-hash": "llama-gguf-hash",
    "cvector-generator": "llama-cvector-generator",
    "fit-params": "llama-fit-params",
    "idle": "llama-idle",
    "eval-callback": "llama-eval-callback",
    "vdot": "llama-vdot",
    "q8dot": "llama-q8dot",
    "results": "llama-results",
    "template-analysis": "llama-template-analysis",
    "simple": "llama-simple",
    "simple-chat": "llama-simple-chat",
    "mtmd-cli": "llama-mtmd-cli",
    "llava-cli": "llama-llava-cli",
    "qwen2vl-cli": "llama-qwen2vl-cli",
    "gemma3-cli": "llama-gemma3-cli",
    "minicpmv-cli": "llama-minicpmv-cli",
    "diffusion-cli": "llama-diffusion-cli",
}

TEST_NAMES = {
    "chat",
    "backend-ops",
    "jinja",
    "peg-parser",
    "alloc",
    "quantize-perf",
    "rope",
    "state-restore-fragmented",
    "autorelease",
    "model-load-cancel",
    "gguf",
    "opt",
    "chat-template",
    "arg-parser",
    "json-schema-to-grammar",
    "json-partial",
    "log",
    "quantize-stats",
    "grammar-integration",
    "llama-archs",
    "sampling",
    "tokenizer-0",
    "llama-grammar",
    "grammar-parser",
    "tokenizer-1-bpe",
    "reasoning-budget",
    "tokenizer-1-spm",
    "gbnf-validator",
    "c",
    "chat-auto-parser",
}


def _resolve_bin_dir() -> Path:
    active_version = get_active_version()
    if active_version is None:
        print("Error: No active llama.cpp version set. Run 'nlp use <version>' to set one.", file=sys.stderr)
        sys.exit(1)

    version_dir = get_version_dir(active_version)
    if not version_dir.exists():
        print(f"Error: Active version {active_version} is not installed. Run 'nlp install {active_version}' to install it.", file=sys.stderr)
        sys.exit(1)

    return version_dir


def run_binary(binary_name: str, profile_id: str, extra_args: list[str]) -> None:
    """Resolve profile and exec the binary."""
    bin_dir = _resolve_bin_dir()
    binary_path = bin_dir / binary_name
    if not binary_path.exists():
        print(f"Error: {binary_name} not found. Run 'nlp install' to reinstall.", file=sys.stderr)
        sys.exit(1)

    profile = get_profile(profile_id)
    model_path = profile["model_path"]
    system_prompt = profile.get("system_prompt")
    args_str = profile.get("args")

    argv = [str(binary_path), "-m", model_path]
    if system_prompt:
        if binary_name == "llama-server":
            print(
                "Warning: system_prompt is set but --system-prompt is not supported by llama-server. Skipping.",
                file=sys.stderr,
            )
        else:
            argv += ["--system-prompt", system_prompt]
    if args_str:
        argv += shlex.split(args_str)
    argv += extra_args

    env = os.environ.copy()
    ld_path = env.get("LD_LIBRARY_PATH", "")
    if ld_path:
        env["LD_LIBRARY_PATH"] = f"{bin_dir}:{ld_path}"
    else:
        env["LD_LIBRARY_PATH"] = str(bin_dir)

    os.execvpe(str(binary_path), argv, env)