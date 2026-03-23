from __future__ import annotations

from typing import Any


class NovelCtlError(Exception):
    default_code = "NovelCtlError"
    default_hint = "检查命令输入、工作区状态和相关配置。"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        hint: str | None = None,
        details: dict[str, Any] | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(message)
        self.code = code or self.default_code
        self.hint = hint or self.default_hint
        self.details = details or {}
        self.exit_code = exit_code

    def payload(self) -> dict[str, Any]:
        error: dict[str, Any] = {
            "code": self.code,
            "message": str(self),
            "hint": self.hint,
        }
        if self.details:
            error["details"] = self.details
        return {"error": error}


class WorkspaceError(NovelCtlError):
    default_code = "WorkspaceError"
    default_hint = "检查工作区路径、目录结构和模板资源是否存在。"


class ConfigError(NovelCtlError):
    default_code = "ConfigError"
    default_hint = "检查 `.novel/config.yaml` 是否存在且为合法 YAML 映射。"


class ValidationError(NovelCtlError):
    default_code = "ValidationError"
    default_hint = "检查命令输入、源文件格式和结构化字段。"


class ThresholdError(ValidationError):
    default_code = "ThresholdError"
    default_hint = "当前归档条件未满足；可先修复条件，或确认后再使用 `--force`。"


class NotFoundError(NovelCtlError):
    default_code = "NotFoundError"
    default_hint = "检查输入标识是否存在，或先列出可用对象。"


class SceneNotFoundError(NotFoundError):
    default_code = "SceneNotFoundError"
    default_hint = "检查 `scene_id` 是否正确，或先运行 `novelctl retrieve text <workspace> --browse` 浏览可用场景。"
