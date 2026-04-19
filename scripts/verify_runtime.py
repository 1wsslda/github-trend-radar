#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd or PROJECT_ROOT), check=True)


def python_sources() -> list[str]:
    roots = [
        SRC_ROOT / "gitsonar" / "runtime",
        SRC_ROOT / "gitsonar" / "runtime_github",
        SRC_ROOT / "gitsonar" / "runtime_ui",
    ]
    files = [
        SRC_ROOT / "gitsonar" / "__init__.py",
        SRC_ROOT / "gitsonar" / "__main__.py",
    ]
    for root in roots:
        files.extend(sorted(root.rglob("*.py")))
    return [str(path) for path in files]


def verify_python_syntax() -> None:
    run([sys.executable, "-m", "py_compile", *python_sources()])


def verify_runtime_js() -> None:
    node = shutil.which("node")
    if not node:
        print("node not found; skipping explicit runtime JS syntax check")
        return
    sys.path.insert(0, str(SRC_ROOT))
    from gitsonar.runtime_ui.assets import JS  # pylint: disable=import-outside-toplevel

    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(JS)
        temp_path = Path(handle.name)
    try:
        run([node, "--check", str(temp_path)])
    finally:
        temp_path.unlink(missing_ok=True)


def verify_tests() -> None:
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"])


def main() -> None:
    verify_python_syntax()
    verify_runtime_js()
    verify_tests()


if __name__ == "__main__":
    main()
