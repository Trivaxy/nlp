"""Build management for llama.cpp."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import requests

from .versions import normalize_version, is_version_installed, get_version_dir

LLAMA_REPO = "https://github.com/ggml-org/llama.cpp"
LLAMA_SRC_DIR = Path(__file__).parent / "llama.cpp"
BUILD_DIR = LLAMA_SRC_DIR / "build"


def has_cuda() -> bool:
    """Check if CUDA toolkit (nvcc) is available in PATH."""
    return shutil.which("nvcc") is not None


def has_vulkan() -> bool:
    """Check if Vulkan SDK is available by looking for vulkaninfo."""
    return shutil.which("vulkaninfo") is not None


def download_llama_cpp(version: str) -> None:
    """Download and extract llama.cpp source tarball for the given version."""
    print(f"Downloading llama.cpp {version}...")
    if LLAMA_SRC_DIR.exists():
        shutil.rmtree(LLAMA_SRC_DIR)

    tarball_url = f"{LLAMA_REPO}/archive/refs/tags/{version}.tar.gz"
    resp = requests.get(tarball_url, timeout=120, stream=True)
    resp.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        for chunk in resp.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        with tarfile.open(tmp_path, mode="r:gz") as tar:
            tar.extractall(path=LLAMA_SRC_DIR.parent, filter="data")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    src_archive = LLAMA_SRC_DIR.parent / f"llama.cpp-{version}"
    if src_archive.exists():
        src_archive.rename(LLAMA_SRC_DIR)


def build_llama_cpp(*, backends: list[str]) -> None:
    """Configure and build llama.cpp with CMake."""
    print("Configuring llama.cpp with CMake...")
    cmake_args = ["cmake", "-B", str(BUILD_DIR)]
    if "cuda" in backends:
        cmake_args.append("-DGGML_CUDA=ON")
    if "vulkan" in backends:
        cmake_args.append("-DGGML_VULKAN=ON")
    cmake_args.append("-DGGML_NATIVE=ON")

    subprocess.run(cmake_args, cwd=str(LLAMA_SRC_DIR), check=True)

    nproc = os.cpu_count() or 1
    print(f"Building llama.cpp with {nproc} parallel jobs...")
    subprocess.run(
        ["cmake", "--build", str(BUILD_DIR), "--config", "Release", "-j", str(nproc)],
        cwd=str(LLAMA_SRC_DIR),
        check=True,
    )


def collect_artifacts(version: str) -> None:
    """Copy all built binaries from build/bin/ to the version-specific directory."""
    print("Collecting build artifacts...")
    bin_dir = BUILD_DIR / "bin"
    if not bin_dir.exists():
        print("Error: build/bin/ directory not found after build.", file=sys.stderr)
        sys.exit(1)

    version_dir = get_version_dir(version)
    if version_dir.exists():
        shutil.rmtree(version_dir)
    version_dir.mkdir(parents=True)

    for item in bin_dir.iterdir():
        dest = version_dir / item.name
        if item.is_dir():
            shutil.copytree(str(item), str(dest))
        else:
            shutil.copy2(str(item), str(dest))

    print(f"Artifacts copied to {version_dir}/")


def cleanup_src() -> None:
    """Remove the downloaded llama.cpp source directory."""
    if LLAMA_SRC_DIR.exists():
        print("Cleaning up source directory...")
        shutil.rmtree(LLAMA_SRC_DIR)


def do_build(*, backends: list[str] | None = None, version: str) -> None:
    """Orchestrate download, build, collect, and cleanup."""
    if backends is None:
        if has_cuda():
            backends = ["cuda"]
        elif has_vulkan():
            backends = ["vulkan"]
        else:
            print("Error: No CUDA or Vulkan detected. Please specify --backends.", file=sys.stderr)
            sys.exit(1)

    try:
        download_llama_cpp(version)
        build_llama_cpp(backends=backends)
        collect_artifacts(version)
    finally:
        cleanup_src()

    print(f"Successfully built llama.cpp {version}.")