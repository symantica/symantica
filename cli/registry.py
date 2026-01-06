from __future__ import annotations

import sys

from core.compiler.load import load_project
from core.compiler.registry import build_registry, write_registry
from core.compiler.validate import validate_project


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]

    if not argv:
        print("Usage: symantica build-registry <project.yaml> [--out registry.json] [--lock registry.lock.json]")
        return 2

    project_path = argv[0]
    out_path = None
    lock_path = None

    if "--out" in argv:
        idx = argv.index("--out")
        if idx + 1 >= len(argv):
            print("[ERROR] Missing value for --out")
            return 2
        out_path = argv[idx + 1]

    if "--lock" in argv:
        idx = argv.index("--lock")
        if idx + 1 >= len(argv):
            print("[ERROR] Missing value for --lock")
            return 2
        lock_path = argv[idx + 1]

    out_path = out_path or "registry.json"
    lock_path = lock_path or "registry.lock.json"

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

    reg = build_registry(project, deterministic=False)
    p1 = write_registry(reg, out_path)

    lock = build_registry(project, deterministic=True)
    p2 = write_registry(lock, lock_path)

    print(f"Registry written: {p1}")
    print(f"Registry lock written: {p2}")
    return 0
