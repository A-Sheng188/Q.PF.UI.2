#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate a full directory tree of current repo into DIR.txt at repo root.

Run (from repo root):
  python tools/gen.DIR.txt.py

It will:
  - auto-detect repo root (git or .git directory)
  - write DIR.txt at repo root
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import List, Set


DEFAULT_IGNORE_DIRS: Set[str] = {
    ".git",
    ".vscode",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

DEFAULT_IGNORE_FILES: Set[str] = {
    ".DS_Store",
}

INCLUDE_HIDDEN = True


def detect_repo_root(start: Path) -> Path:
    """
    Prefer: `git rev-parse --show-toplevel`
    Fallback: walk up parents until .git directory exists
    """
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(start),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if out:
            return Path(out).resolve()
    except Exception:
        pass

    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / ".git").exists():
            return p
    # last resort: use start
    return start.resolve()


def should_ignore(path: Path) -> bool:
    name = path.name

    if path.is_dir():
        if name in DEFAULT_IGNORE_DIRS:
            return True
        if not INCLUDE_HIDDEN and name.startswith("."):
            return True
    else:
        if name in DEFAULT_IGNORE_FILES:
            return True
        if not INCLUDE_HIDDEN and name.startswith("."):
            return True

    return False


def list_children_sorted(p: Path) -> List[Path]:
    try:
        children = list(p.iterdir())
    except PermissionError:
        return []

    children = [c for c in children if not should_ignore(c)]
    children.sort(key=lambda x: (0 if x.is_dir() else 1, x.name.lower()))
    return children


def render_tree(root: Path) -> List[str]:
    lines: List[str] = []
    root_name = root.name if root.name else str(root)
    lines.append(root_name + "/")

    def walk(dir_path: Path, prefix: str) -> None:
        children = list_children_sorted(dir_path)
        count = len(children)
        for idx, child in enumerate(children):
            is_last = idx == (count - 1)
            branch = "└── " if is_last else "├── "
            next_prefix = prefix + ("    " if is_last else "│   ")

            if child.is_dir():
                lines.append(f"{prefix}{branch}{child.name}/")
                walk(child, next_prefix)
            else:
                lines.append(f"{prefix}{branch}{child.name}")

    walk(root, "")
    return lines


def main() -> None:
    cwd = Path(os.getcwd())
    repo_root = detect_repo_root(cwd)
    out_file = repo_root / "DIR.txt"

    tree_lines = render_tree(repo_root)
    content = "\n".join(tree_lines).rstrip() + "\n"
    out_file.write_text(content, encoding="utf-8")

    print(f"[OK] Repo root: {repo_root}")
    print(f"[OK] Wrote: {out_file}")


if __name__ == "__main__":
    main()
