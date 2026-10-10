"""Structural package checks; these do not measure model behavior."""

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

TOKEN = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
# These files deliberately use simple inline Markdown links without titles.
LINK = re.compile(r"\[[^\]\n]+\]\(([^\s)]+)\)")


def local_targets(document: Path, boundary: Path) -> set[Path]:
    """Resolve package-local links and check casing even on case-insensitive OSes."""
    boundary = boundary.resolve()
    targets = set()
    for raw in LINK.findall(document.read_text(encoding="utf-8")):
        url = urlsplit(raw)
        if url.scheme or url.netloc or not url.path:
            continue
        path = (document.parent / unquote(url.path)).resolve()
        try:
            parts = path.relative_to(boundary).parts
        except ValueError as exc:
            raise ValueError(f"Link escapes package: {document}: {raw}") from exc
        current = boundary
        for part in parts:
            if not current.is_dir() or part not in {p.name for p in current.iterdir()}:
                raise ValueError(f"Missing or case-mismatched link: {document}: {raw}")
            current /= part
        if not current.exists():
            raise ValueError(f"Missing link: {document}: {raw}")
        targets.add(path)
    return targets


def reachable_resources(root: Path) -> set[Path]:
    """Follow explicit Markdown edges without loading unlinked siblings."""
    root = root.resolve()
    pending = [root / "SKILL.md"]
    reached = set()
    while pending:
        current = pending.pop()
        if current in reached:
            continue
        reached.add(current)
        if current.is_file() and current.name.endswith((".md", ".md.tmpl")):
            pending.extend(local_targets(current, root) - reached)
    return reached


def check_resources(root: Path) -> None:
    """Validate reachable package resources, including reference-to-asset links."""
    root = root.resolve()
    if not (root / "SKILL.md").is_file():
        raise ValueError(f"Missing entrypoint: {root}")
    resources = {
        p.resolve()
        for name in ("references", "assets", "scripts")
        for p in (root / name).rglob("*")
        if p.is_file()
    }
    reached = reachable_resources(root)
    if resources - reached:
        raise ValueError(f"Unrouted resources: {resources - reached}")
    # Native metadata and licenses are not model-loaded references; still check
    # every Markdown document's local links, not just selected route examples.
    for document in root.rglob("*"):
        if document.is_file() and document.name.endswith((".md", ".md.tmpl")):
            local_targets(document, root)


def render_template(text: str, values: dict[str, str]) -> str:
    """Instantiate a test asset; fail instead of publishing missing fields."""
    missing = set(TOKEN.findall(text)) - values.keys()
    if missing:
        raise ValueError(f"Missing template fields: {sorted(missing)}")
    output = TOKEN.sub(lambda match: values[match.group(1)], text)
    if "{{" in output or "}}" in output:
        raise ValueError("Unresolved or malformed template placeholder")
    return output
