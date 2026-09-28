from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
import shutil
import time
import uuid
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = SKILL_ROOT / ".runtime"
LOG_PATH = RUNTIME_DIR / "browser.log"
BROKER_STATE_PATH = RUNTIME_DIR / "broker.json"
OPERATION_LOCK_PATH = RUNTIME_DIR / "operation.lock"

IDLE_SECONDS = int(os.environ.get("NEXUM_BROWSER_IDLE_SECONDS", "3600"))
REQUEST_TIMEOUT_SECONDS = int(
    os.environ.get("NEXUM_BROWSER_REQUEST_TIMEOUT_SECONDS", "45")
)
LOCK_STALE_SECONDS = int(
    os.environ.get("NEXUM_BROWSER_LOCK_STALE_SECONDS", "900")
)


@contextlib.contextmanager
def operation_lock(timeout: float = REQUEST_TIMEOUT_SECONDS + 15):
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    deadline = time.monotonic() + timeout

    while True:
        try:
            fd = os.open(
                OPERATION_LOCK_PATH,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError:
            try:
                age = time.time() - OPERATION_LOCK_PATH.stat().st_mtime
            except FileNotFoundError:
                continue
            if age > LOCK_STALE_SECONDS:
                with contextlib.suppress(FileNotFoundError):
                    OPERATION_LOCK_PATH.unlink()
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError("Another nexum-browser operation is still running")
            time.sleep(0.05)
            continue

        try:
            os.write(fd, token.encode("ascii"))
        finally:
            os.close(fd)
        break

    try:
        yield
    finally:
        try:
            if OPERATION_LOCK_PATH.read_text(encoding="ascii") == token:
                OPERATION_LOCK_PATH.unlink()
        except (FileNotFoundError, OSError, UnicodeDecodeError):
            pass


def emit(value: dict[str, Any]) -> None:
    # Keep stdout portable across Windows console code pages.
    print(json.dumps(value, ensure_ascii=True, separators=(",", ":")))


def fail(
    code: str,
    message: str,
    *,
    retryable: bool = False,
    data: dict[str, Any] | None = None,
    exit_code: int = 1,
) -> None:
    value: dict[str, Any] = {
        "code": code,
        "message": message,
        "retryable": retryable,
    }
    if data is not None:
        value["data"] = data
    emit(value)
    raise SystemExit(exit_code)


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex")).expanduser()


def is_executable_file(path: Path) -> bool:
    return path.is_file() and (os.name == "nt" or os.access(path, os.X_OK))


def find_codex() -> Path:
    override = os.environ.get("NEXUM_BROWSER_CODEX")
    if override:
        candidate = Path(override).expanduser()
        if is_executable_file(candidate):
            return candidate
        found = shutil.which(override)
        if found:
            return Path(found)
        raise RuntimeError(f"NEXUM_BROWSER_CODEX is not executable: {override}")

    found = shutil.which("codex")
    if found:
        return Path(found)
    raise RuntimeError("Codex CLI was not found in PATH")


def find_browser_plugin_root(runtime_version: str | None = None) -> Path:
    root = codex_home() / "plugins/cache/openai-bundled/browser"
    if runtime_version:
        exact = root / runtime_version
        if (exact / ".codex-plugin/plugin.json").is_file():
            return exact

    candidates = [
        marker.parent.parent
        for marker in root.glob("*/.codex-plugin/plugin.json")
        if marker.is_file()
    ]
    if not candidates:
        raise RuntimeError(f"OpenAI Browser plugin was not found under {root}")
    return max(
        candidates,
        key=lambda path: (path / ".codex-plugin/plugin.json").stat().st_mtime_ns,
    )


def parse_json_output(value: str) -> dict[str, Any]:
    text = value.strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def run_json_script(
    node: Path,
    script: Path,
    *args: str,
    timeout: float = 20,
) -> tuple[int, dict[str, Any], str]:
    import subprocess

    result = subprocess.run(
        [str(node), str(script), *args],
        cwd=str(script.parent.parent),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    value = parse_json_output(result.stdout)
    message = (result.stderr or result.stdout).strip()
    return result.returncode, value, message
