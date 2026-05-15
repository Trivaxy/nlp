from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def nlp_config_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        old = os.environ.get("NLP_CONFIG_DIR")
        os.environ["NLP_CONFIG_DIR"] = tmpdir
        yield Path(tmpdir)
        if old is None:
            del os.environ["NLP_CONFIG_DIR"]
        else:
            os.environ["NLP_CONFIG_DIR"] = old


@pytest.fixture
def model_file(tmp_path: Path) -> Path:
    path = tmp_path / "model.gguf"
    path.write_text("dummy model content")
    return path


def run_nlp(*args: str, nlp_config_dir: Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if nlp_config_dir is not None:
        env["NLP_CONFIG_DIR"] = str(nlp_config_dir)
    return subprocess.run(
        ["uv", "run", "nlp", *args],
        capture_output=True,
        text=True,
        env=env,
    )
