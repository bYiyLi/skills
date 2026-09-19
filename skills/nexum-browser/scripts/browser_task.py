#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True


SKILL_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = SKILL_ROOT / ".runtime" / "broker-task-env.json"


def _load_environment() -> None:
    try:
        value = json.loads(ENV_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(
            f"nexum-browser broker task environment is unavailable: {ENV_PATH}"
        ) from exc
    if not isinstance(value, dict):
        raise RuntimeError("nexum-browser broker task environment is invalid")
    for name, setting in value.items():
        if isinstance(name, str) and isinstance(setting, str):
            os.environ[name] = setting
    with contextlib.suppress(FileNotFoundError):
        ENV_PATH.unlink()


def main() -> int:
    _load_environment()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from nexum_browser.broker import daemon_main

    return daemon_main()


if __name__ == "__main__":
    raise SystemExit(main())
