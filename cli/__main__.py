from __future__ import annotations

import sys

from cli.validate import main as validate_main
from cli.registry import main as registry_main


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: symantica <command> [args]\n"
            "Commands:\n"
            "  validate\n"
            "  build-registry"
        )
        return 2

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "validate":
        return validate_main(args)

    if cmd == "build-registry":
        return registry_main(args)

    print(f"Unknown command: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
