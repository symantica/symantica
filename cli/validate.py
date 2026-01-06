from __future__ import annotations

import sys

from core.compiler.load import load_project
from core.compiler.validate import validate_project


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if not argv:
        print("Usage: symantica validate <path-to-project.yaml>")
        return 2

    path = argv[0]
    try:
        project = load_project(path)
    except Exception as e:
        print(f"[ERROR] Failed to load project spec: {e}")
        return 2

    issues = validate_project(project)
    errors = [i for i in issues if i.level == "ERROR"]
    warns = [i for i in issues if i.level == "WARN"]

    for w in warns:
        print(f"[WARN] {w.message}\n")

    for e in errors:
        print(f"[ERROR] {e.message}\n")

    if errors:
        print(f"Validation failed: {len(errors)} error(s), {len(warns)} warning(s).")
        return 1

    print(f"Validation passed: {len(warns)} warning(s).")
    return 0
