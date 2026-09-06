"""Read-only Python detection for Windows-first deployments."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


def check(command: list[str]) -> dict | None:
    executable = shutil.which(command[0])
    if not executable:
        return None
    try:
        result = subprocess.run([executable, *command[1:], "--version"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as error:
        return {"command": command, "path": executable, "error": str(error)}
    output = (result.stdout or result.stderr).strip()
    if result.returncode != 0 or not output.lower().startswith("python"):
        return None
    return {"command": command, "path": str(Path(executable).resolve()), "version": output}


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Python environment check")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--repair-path", action="store_true", help="kept for compatibility; never changes PATH")
    parser.add_argument("--install", action="store_true", help="reports that user-approved installation is required")
    args = parser.parse_args()
    checks = [check(["python"]), check(["py", "-3"]), check(["python3"])]
    match = next((item for item in checks if item and "version" in item), None)
    result = {
        "available": bool(match),
        "match": match,
        "checked": [item for item in checks if item],
        "pathChanged": False,
        "message": "Python is available." if match else "No Python 3 interpreter found; request approval before installing one.",
    }
    if args.repair_path:
        result["message"] += " PATH repair is intentionally manual in this package."
    if args.install:
        result["message"] += " Use an approved offline installer; this script never downloads or executes installers."
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
    raise SystemExit(0 if match else 1)


if __name__ == "__main__":
    main()
