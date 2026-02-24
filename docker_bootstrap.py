"""Docker bootstrap script.

Prepares fork branch in persistent volume and starts docker launcher.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys


def _require_env(name: str) -> str:
    value = (os.environ.get(name) or "").strip()
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def _run(cmd: list[str], cwd: pathlib.Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=check)


def _main() -> None:
    # Runtime secrets/config required by launcher.
    for key in (
        "TELEGRAM_BOT_TOKEN",
        "TOTAL_BUDGET",
        "GITHUB_TOKEN",
        "GITHUB_USER",
        "GITHUB_REPO",
    ):
        _require_env(key)

    github_token = _require_env("GITHUB_TOKEN")
    github_user = _require_env("GITHUB_USER")
    github_repo = _require_env("GITHUB_REPO")

    boot_branch = (os.environ.get("OUROBOROS_BOOT_BRANCH") or "ouroboros").strip()
    repo_dir = pathlib.Path(os.environ.get("REPO_DIR") or "/data/ouroboros_repo").resolve()
    drive_root = pathlib.Path(os.environ.get("DRIVE_ROOT") or "/data/Ouroboros").resolve()
    remote_url = f"https://{github_token}:x-oauth-basic@github.com/{github_user}/{github_repo}.git"

    os.environ["REPO_DIR"] = str(repo_dir)
    os.environ["DRIVE_ROOT"] = str(drive_root)
    os.environ.setdefault("OUROBOROS_REPO_DIR", str(repo_dir))
    os.environ.setdefault("OUROBOROS_DRIVE_ROOT", str(drive_root))
    os.environ.setdefault("OUROBOROS_SKIP_RUNTIME_PIP", "1")

    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    drive_root.mkdir(parents=True, exist_ok=True)

    if not (repo_dir / ".git").exists():
        _run(["rm", "-rf", str(repo_dir)], check=False)
        _run(["git", "clone", remote_url, str(repo_dir)])
    else:
        _run(["git", "remote", "set-url", "origin", remote_url], cwd=repo_dir)

    _run(["git", "fetch", "origin"], cwd=repo_dir)

    has_boot_branch = (
        subprocess.run(
            ["git", "rev-parse", "--verify", f"origin/{boot_branch}"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )
    if has_boot_branch:
        # Use explicit branch creation/reset to avoid ambiguity with same-named paths.
        _run(["git", "checkout", "-B", boot_branch, "--track", f"origin/{boot_branch}"], cwd=repo_dir)
        _run(["git", "reset", "--hard", f"origin/{boot_branch}"], cwd=repo_dir)
    else:
        print(f"[boot] branch {boot_branch} not found on fork, creating from origin/main")
        _run(["git", "checkout", "-b", boot_branch, "origin/main"], cwd=repo_dir)
        _run(["git", "push", "-u", "origin", boot_branch], cwd=repo_dir)
        stable = f"{boot_branch}-stable"
        _run(["git", "branch", stable], cwd=repo_dir)
        _run(["git", "push", "-u", "origin", stable], cwd=repo_dir)

    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_dir), text=True).strip()
    print(f"[boot] branch={boot_branch} sha={head_sha[:12]}")
    print(f"[boot] drive_root={drive_root}")
    print(f"[boot] logs={drive_root / 'logs' / 'supervisor.jsonl'}")

    launcher_path = repo_dir / "docker_launcher.py"
    if not launcher_path.exists():
        fallback_launcher = repo_dir / "colab_launcher.py"
        if fallback_launcher.exists():
            launcher_path = fallback_launcher
            print(f"[boot] docker_launcher.py not found, using fallback: {launcher_path.name}")
        else:
            raise RuntimeError(
                f"Missing launchers in cloned repo: {repo_dir / 'docker_launcher.py'} and {fallback_launcher}"
            )

    _run([sys.executable, str(launcher_path)], cwd=repo_dir)


if __name__ == "__main__":
    _main()

