"""Docker/VPS runtime launcher.

Sets Docker-friendly defaults, then runs the main launcher logic.
"""

from __future__ import annotations

import os


def _set_default_env() -> None:
    os.environ.setdefault("DRIVE_ROOT", "/data/Ouroboros")
    os.environ.setdefault("REPO_DIR", "/data/ouroboros_repo")
    os.environ.setdefault("OUROBOROS_DRIVE_ROOT", os.environ["DRIVE_ROOT"])
    os.environ.setdefault("OUROBOROS_REPO_DIR", os.environ["REPO_DIR"])

    # In Docker dependencies must be preinstalled in the image.
    os.environ.setdefault("OUROBOROS_SKIP_RUNTIME_PIP", "1")
    os.environ.setdefault("OUROBOROS_WORKER_START_METHOD", "fork")
    os.environ.setdefault("OUROBOROS_DIAG_HEARTBEAT_SEC", "30")
    os.environ.setdefault("OUROBOROS_DIAG_SLOW_CYCLE_SEC", "20")
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    os.environ.setdefault("OUROBOROS_LLM_BASE_URL", "http://host.docker.internal:1234/v1")
    os.environ.setdefault("OUROBOROS_LLM_API_KEY", "lm-studio")
    os.environ.setdefault("OUROBOROS_MODEL", "qwen/qwen3-30b-a3b-2507")


_set_default_env()

# Reuse the existing launcher logic (event loop, supervisor wiring, etc.).
import colab_launcher  # noqa: F401,E402

