#!/usr/bin/env python3
"""Lightweight verification for the resume helper scripts.

Checks:
- Python syntax compilation for both scripts.
- `--help` smoke tests for both CLIs.
- Safe no-argument behavior (usage error, no side effects).

This keeps verification dependency-light and runnable from PowerShell:

    python scripts/verify_scripts.py
"""

from __future__ import annotations

import py_compile
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = (
    ROOT / "scripts" / "render_resume_pdf.py",
    ROOT / "scripts" / "remove_photo_background.py",
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def compile_script(path: Path) -> CheckResult:
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        return CheckResult(path.name, False, str(exc))
    return CheckResult(path.name, True, "compiled")


def run_command(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def smoke_help(path: Path) -> CheckResult:
    result = run_command([str(path.relative_to(ROOT)), "--help"])
    if result.returncode != 0:
        return CheckResult(path.name, False, f"exit={result.returncode} stderr={result.stderr.strip()}")
    if "usage:" not in result.stdout.lower():
        return CheckResult(path.name, False, "help output missing usage text")
    return CheckResult(path.name, True, "help OK")


def smoke_no_args(path: Path) -> CheckResult:
    result = run_command([str(path.relative_to(ROOT))])
    if result.returncode == 0:
        return CheckResult(path.name, False, "expected usage failure, got success")
    merged = f"{result.stdout}\n{result.stderr}".lower()
    if "usage:" not in merged and "error:" not in merged:
        return CheckResult(path.name, False, "missing argparse usage/error output")
    return CheckResult(path.name, True, f"usage failure exit={result.returncode}")


def print_result(prefix: str, result: CheckResult) -> None:
    status = "PASS" if result.ok else "FAIL"
    print(f"{status} {prefix} {result.name}: {result.detail}")


def main() -> int:
    results = []

    for script in SCRIPTS:
        compile_result = compile_script(script)
        print_result("compile", compile_result)
        results.append(compile_result)

        help_result = smoke_help(script)
        print_result("help", help_result)
        results.append(help_result)

        no_args_result = smoke_no_args(script)
        print_result("no-args", no_args_result)
        results.append(no_args_result)

    failed = [result for result in results if not result.ok]
    if failed:
        print(f"\n{len(failed)} check(s) failed.")
        return 1

    print("\nAll script verification checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
