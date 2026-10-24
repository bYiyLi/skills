#!/usr/bin/env python3
"""Build self-contained private plugin ZIPs from the repository's Skill sources."""
import argparse
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "development-standards": ("develop-software", "prompt-authoring-spec", "skill-authoring-spec"),
    "nexum-development": ("nexum-chatgpt-development",),
}

def collect(target, app_id=None):
    if target not in TARGETS:
        raise ValueError("Unknown plugin")
    if app_id and target != "nexum-development":
        raise ValueError("The general plugin must not bind an app")
    if app_id and not re.fullmatch(r"(?:asdk_app_|connector_|templated_apps_)[A-Za-z0-9][A-Za-z0-9_-]*", app_id):
        raise ValueError("Expected a verified app ID, not a plugin ID or URL")
    folder = ROOT / "plugins" / target
    manifest = json.loads((folder / "plugin.json").read_text(encoding="utf-8"))
    result = {}
    for skill in TARGETS[target]:
        source = ROOT / "skills" / skill
        if not (source / "SKILL.md").is_file():
            raise ValueError(f"Missing Skill: {skill}")
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"Symlink not allowed: {path}")
            if not path.is_file():
                continue
            relative = path.relative_to(source)
            if any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
                continue
            data = path.read_bytes()
            if relative.as_posix() == "agents/openai.yaml":
                # Keep display metadata; omit optional Codex-specific starter text.
                data = ("\n".join(line for line in data.decode("utf-8").splitlines()
                                  if not line.lstrip().startswith("default_prompt:")) + "\n").encode()
            result[f"skills/{skill}/{relative.as_posix()}"] = data
    if target == "nexum-development":
        entry = "skills/nexum-chatgpt-development/SKILL.md"
        body = result[entry].decode("utf-8")
        heading = "# Nexum ChatGPT Development"
        if body.count(heading) != 1:
            raise ValueError("Nexum entrypoint changed; review the packaging adapter")
        body = body.replace(heading, heading + "\n\nFor this ChatGPT plugin, first read "
                            "[plugin integration](references/chatgpt-plugin.md) "
                            "for cross-plugin discovery and resource locations.", 1)
        result[entry] = body.encode()
        result["skills/nexum-chatgpt-development/references/chatgpt-plugin.md"] = (
            folder / "chatgpt-resources.md").read_bytes()
    extension = manifest["extensions"]["com.openai"]
    if app_id:
        extension["apps"] = "./.app.json"
        result[".app.json"] = (json.dumps({"apps": {"nexum": {"id": app_id}}}, indent=2) + "\n").encode()
    result["plugin.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    validate(result, target)
    return result

def validate(files, target):
    manifest = json.loads(files["plugin.json"])
    if manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        raise ValueError("Invalid portable manifest schema")
    if manifest["name"] != target or not re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"]):
        raise ValueError("Invalid identity/version")
    entries = {p.split("/")[1] for p in files if p.endswith("/SKILL.md")}
    if entries != set(TARGETS[target]):
        raise ValueError("Unexpected or missing skills")
    if target == "development-standards" and (".app.json" in files or "apps" in manifest["extensions"]["com.openai"]):
        raise ValueError("General plugin has an app dependency")
    for name, data in files.items():
        if name.startswith("/") or ".." in Path(name).parts:
            raise ValueError("Unsafe archive path")
        if name.endswith("/SKILL.md"):
            text = data.decode("utf-8")
            if not text.startswith("---\n") or len(data) > 1024 * 1024:
                raise ValueError("Invalid Skill entrypoint")
        if name.endswith((".md", ".tmpl")):
            for link in re.findall(r"\]\(([^)]+)\)", data.decode("utf-8")):
                if link.startswith(("https:", "http:", "#")):
                    continue
                parts = list(Path(name).parent.parts)
                for item in link.split("#")[0].split("/"):
                    if item == "..":
                        if not parts:
                            raise ValueError("Resource escapes plugin")
                        parts.pop()
                    elif item not in ("", "."):
                        parts.append(item)
                if "/".join(parts) not in files:
                    raise ValueError(f"Missing resource: {name} -> {link}")

def build(target, output, app_id=None):
    files = collect(target, app_id)
    manifest = json.loads(files["plugin.json"])
    output = Path(output).resolve()
    if output.is_relative_to(ROOT / "skills") or any(
        output.is_relative_to(ROOT / "plugins" / item) for item in TARGETS):
        raise ValueError("Output must be outside source package directories")
    output.mkdir(parents=True, exist_ok=True)
    suffix = "-personal" if app_id else ""
    destination = output / f"{target}-{manifest['version']}{suffix}.zip"
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return destination

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=(*TARGETS, "all"))
    parser.add_argument("--output", type=Path, default=ROOT / "plugins" / "dist")
    parser.add_argument("--nexum-app-id", help="Verified current-account app ID; creates a private account-specific package")
    args = parser.parse_args()
    if args.nexum_app_id and args.target != "nexum-development":
        parser.error("--nexum-app-id is only valid for nexum-development")
    for target in TARGETS if args.target == "all" else (args.target,):
        print(build(target, args.output, args.nexum_app_id))
