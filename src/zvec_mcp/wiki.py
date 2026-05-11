"""Read-only helpers for Obsidian-style markdown wiki navigation."""

from __future__ import annotations

import fnmatch
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

WIKILINK_RE = re.compile(r"\[\[([^\]]+?)\]\]")


@dataclass(frozen=True)
class WikiLink:
    """A parsed Obsidian wikilink."""

    raw: str
    target: str
    label: str | None = None
    heading: str | None = None


def normalize_wikilink_target(raw: str) -> WikiLink:
    """Parse a raw wikilink or bare target into normalized pieces."""
    value = raw.strip()
    if value.startswith("[[") and value.endswith("]]"):
        value = value[2:-2].strip()

    target_part, label = value, None
    if "|" in value:
        target_part, label = value.split("|", 1)
        label = label.strip() or None

    target, heading = target_part.strip(), None
    if "#" in target:
        target, heading = target.split("#", 1)
        heading = heading.strip() or None

    return WikiLink(raw=raw, target=target.strip(), label=label, heading=heading)


def extract_wikilinks(text: str) -> list[WikiLink]:
    """Extract all Obsidian wikilinks from markdown text."""
    return [normalize_wikilink_target(match.group(0)) for match in WIKILINK_RE.finditer(text)]


def find_wiki_root(path: Path) -> Path | None:
    """Find the nearest parent that looks like a wiki root."""
    start = path if path.is_dir() else path.parent
    for parent in (start, *start.parents):
        if (parent / "_backlinks.json").is_file() or (parent / "_index.md").is_file():
            return parent
    return None


def _target_candidates(base: Path, target: str) -> list[Path]:
    """Return target path candidates with Obsidian markdown conveniences."""
    if not target:
        return []
    raw = Path(target).expanduser()
    candidates: list[Path] = []
    first = raw if raw.is_absolute() else base / raw
    candidates.append(first)
    if target.endswith("/"):
        candidates.append(first / "index.md")
    elif first.suffix == "":
        candidates.append(first.with_suffix(".md"))
    return candidates


def resolve_wikilink(source_file: str | Path, target_link: str, root: str | Path | None = None) -> dict[str, Any]:
    """Resolve a wikilink target from a source markdown file."""
    source = Path(source_file).expanduser().resolve()
    link = normalize_wikilink_target(target_link)
    explicit_root = Path(root).expanduser().resolve() if root else None
    wiki_root = explicit_root or find_wiki_root(source)

    search_bases = [source.parent]
    if wiki_root and wiki_root not in search_bases:
        search_bases.append(wiki_root)

    checked: list[str] = []
    for base in search_bases:
        for candidate in _target_candidates(base, link.target):
            resolved = candidate.resolve()
            checked.append(str(resolved))
            if resolved.is_file():
                return {
                    "raw": link.raw,
                    "target": link.target,
                    "label": link.label,
                    "heading": link.heading,
                    "resolved_path": str(resolved),
                    "exists": True,
                    "checked": checked,
                }

    if wiki_root and link.target and "/" not in link.target and not Path(link.target).suffix:
        matches = sorted(wiki_root.rglob(f"{link.target}.md"))
        if matches:
            resolved = matches[0].resolve()
            checked.append(str(resolved))
            return {
                "raw": link.raw,
                "target": link.target,
                "label": link.label,
                "heading": link.heading,
                "resolved_path": str(resolved),
                "exists": True,
                "checked": checked,
            }

    fallback = Path(checked[-1]) if checked else source.parent / link.target
    return {
        "raw": link.raw,
        "target": link.target,
        "label": link.label,
        "heading": link.heading,
        "resolved_path": str(fallback),
        "exists": False,
        "checked": checked,
    }


def _is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def iter_markdown_files(
    root: str | Path,
    glob_pattern: str = "**/*.md",
    exclude_patterns: list[str] | None = None,
    max_files: int | None = None,
) -> list[Path]:
    """List matching markdown files below a root directory."""
    base = Path(root).expanduser().resolve()
    if not base.is_dir():
        raise NotADirectoryError(f"Directory not found: {base}")

    excludes = exclude_patterns or []
    out: list[Path] = []
    for path in sorted(base.glob(glob_pattern)):
        if not path.is_file():
            continue
        rel = path.relative_to(base).as_posix()
        if _is_hidden(Path(rel)):
            continue
        if any(fnmatch.fnmatch(rel, pattern) for pattern in excludes):
            continue
        out.append(path.resolve())
        if max_files is not None and len(out) >= max_files:
            break
    return out


def build_navigation_index(
    root: str | Path,
    *,
    glob_pattern: str = "**/*.md",
    exclude_patterns: list[str] | None = None,
    max_files: int | None = None,
) -> dict[str, Any]:
    """Build a read-only link/backlink index for markdown files."""
    base = Path(root).expanduser().resolve()
    files = iter_markdown_files(base, glob_pattern, exclude_patterns, max_files)
    file_entries: dict[str, Any] = {}
    backlinks: dict[str, list[str]] = {}

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        outgoing = []
        for link in extract_wikilinks(text):
            resolved = resolve_wikilink(path, link.raw, base)
            outgoing.append(resolved)
            if resolved["exists"]:
                backlinks.setdefault(resolved["resolved_path"], []).append(str(path))
        file_entries[str(path)] = {
            "relative_path": path.relative_to(base).as_posix(),
            "outgoing": outgoing,
        }

    return {
        "generated_at": int(time.time()),
        "root": str(base),
        "files": file_entries,
        "backlinks": {key: sorted(set(value)) for key, value in sorted(backlinks.items())},
    }


def write_navigation_index(index: dict[str, Any], output_path: str | Path) -> None:
    """Write a navigation sidecar JSON file."""
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def load_navigation_index(path: str | Path) -> dict[str, Any] | None:
    """Load a navigation sidecar JSON file if it exists."""
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _load_existing_backlinks(source: Path, wiki_root: Path) -> list[str] | None:
    backlinks_file = wiki_root / "_backlinks.json"
    if not backlinks_file.is_file():
        return None
    data = json.loads(backlinks_file.read_text(encoding="utf-8"))
    rel = source.relative_to(wiki_root).as_posix()
    values = data.get(rel)
    if values is None:
        return []
    out = []
    for item in values:
        candidate = (wiki_root / item).resolve()
        out.append(str(candidate))
    return sorted(out)


def backlinks_for(source_file: str | Path, navigation_index_path: str | Path | None = None) -> list[str]:
    """Return backlinks for a file from wiki or sidecar indexes."""
    source = Path(source_file).expanduser().resolve()
    wiki_root = find_wiki_root(source)
    if wiki_root:
        existing = _load_existing_backlinks(source, wiki_root)
        if existing is not None:
            return existing

    if navigation_index_path:
        index = load_navigation_index(navigation_index_path)
        if index:
            return sorted(index.get("backlinks", {}).get(str(source), []))
    return []


def navigate_file(source_file: str | Path, navigation_index_path: str | Path | None = None) -> dict[str, Any]:
    """Read a markdown file and return outgoing links plus backlinks."""
    source = Path(source_file).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"File not found: {source}")

    text = source.read_text(encoding="utf-8", errors="replace")
    wiki_root = find_wiki_root(source)
    root = wiki_root or source.parent
    outgoing = [resolve_wikilink(source, link.raw, root) for link in extract_wikilinks(text)]
    return {
        "source": str(source),
        "wiki_root": str(wiki_root) if wiki_root else None,
        "outgoing": outgoing,
        "backlinks": backlinks_for(source, navigation_index_path),
    }


def retrieve_wikilink(source_file: str | Path, target_link: str) -> dict[str, Any]:
    """Resolve and read a wikilink target."""
    resolved = resolve_wikilink(source_file, target_link)
    content = None
    if resolved["exists"]:
        content = Path(resolved["resolved_path"]).read_text(encoding="utf-8", errors="replace")
    return {**resolved, "content": content}

