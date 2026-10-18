from __future__ import annotations

import json
import os
from pathlib import Path
import re


_WINDOWS_ARGV_SENTINEL = "__NEXUM_BROWSER_WINDOWS_ARGV__"
_WINDOWS_ARGV_ROOT_ENV = "NEXUM_BROWSER_ARGV_ROOT"
_WINDOWS_ARGV_FILE = re.compile(
    r"^nexum-browser-argv-[0-9a-f]{32}\.json$",
    re.IGNORECASE,
)
_SESSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_SESSION_COMMANDS = frozenset({
    "run", "reset", "stop", "status", "doctor",
    "_broker", "_resume", "_cancel",
})


def validate_session(value: str | None) -> str:
    session = (value or "").lower()
    if session == "default":
        raise ValueError("'default' is reserved for the unnamed browser session")
    if session and _SESSION_PATTERN.fullmatch(session) is None:
        raise ValueError(
            "Session must be 1-64 ASCII letters, digits, underscores or "
            "hyphens, starting with a letter or digit"
        )
    return session


def _windows_argv_path(value: str, temp_root: str) -> Path:
    path = Path(value)
    try:
        in_temp_root = os.path.samefile(path.parent, temp_root)
    except OSError:
        in_temp_root = False
    if (
        not in_temp_root
        or _WINDOWS_ARGV_FILE.fullmatch(path.name) is None
        or path.is_symlink()
    ):
        raise RuntimeError(
            "Windows launcher argv path is not a launcher-owned temp file"
        )
    return path


def prepare_argv(argv: list[str]) -> list[str]:
    argsv = list(argv)
    if len(argsv) == 2 and argsv[0] == _WINDOWS_ARGV_SENTINEL:
        temp_root = os.environ.pop(_WINDOWS_ARGV_ROOT_ENV, None)
        if not temp_root:
            raise RuntimeError(
                f"{_WINDOWS_ARGV_ROOT_ENV} is unavailable for Windows launcher"
            )
        path = _windows_argv_path(argsv[1], temp_root)
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RuntimeError(
                f"Windows launcher argv file is unavailable: {exc}"
            ) from exc
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Windows launcher argv file is invalid JSON: {exc}"
            ) from exc
        if not isinstance(parsed, list) or not all(
            isinstance(item, str) for item in parsed
        ):
            raise RuntimeError(
                "Windows launcher argv file must contain a JSON string array"
            )
        argsv = parsed
    return argsv


def select_session(argv: list[str]) -> tuple[list[str], str]:
    argsv = list(argv)
    session = os.environ.get("NEXUM_BROWSER_SESSION")
    if (
        len(argsv) > 1
        and argsv[0] in _SESSION_COMMANDS
        and argsv[1] == "--session"
    ):
        if len(argsv) < 3:
            raise ValueError("--session requires a session name")
        session = argsv[2]
        del argsv[1:3]
    return argsv, validate_session(session)
