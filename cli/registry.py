from __future__ import annotations

import sys

from core.compiler.load import load_project
from core.compiler.registry import build_registry, write_registry
from core.compiler.validate import validate_project


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]

    if not argv:
        print("Usage: symantica build-registry <project.yaml> --out <registry.json>")
        return 2

    project_path = argv[0]
    out_path = None

    # minimal arg parsing
    if "--out" in argv:
        idx = argv.index("--out")
        if idx + 1 >= len(argv):
            print("[ERROR] Missing value for --out")
            return 2
        out_path = argv[idx + 1]

    if not out_path:
        out_path = "registry.json"

    try:
        project = load_project(project_path)
    except Exception as e:
        print(f"[ERROR] Failed to load project spec: {e}")
        return 2

    issues = validate_project(project)
    errors = [i for i in issues if i.level == "ERROR"]
    warns = [i for i in issues if i.level == "WARN"]

    for w in warns:
        print(f"[WARN] {w.message}\n")

    if errors:
        for e in errors:
            print(f"[ERROR] {e.message}\n")
        print(f"Registry build failed: {len(errors)} error(s), {len(warns)} warning(s).")
        return 1

    registry = build_registry(project)
    p = write_registry(registry, out_path)
    print(f"Registry written: {p}")
    return 0
