#!/usr/bin/env python3
"""Disable Homebrew's multi-stage PGO build for one LLVM bottle build.

This is deliberately strict: the one-off workflow is intended only for the exact
LLVM version it names.  If Homebrew changes either the version or the PGO control
line, fail instead of silently building a differently patched formula.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PGO_ASSIGNMENT = (
    "    pgo_build = build.stable? && build.bottle? && OS.mac? && !versioned_formula?"
)
SINGLE_STAGE_ASSIGNMENT = (
    "    pgo_build = false # Intel CI bootstrap: build this bottle in one stage"
)
VERSION_PATTERN = re.compile(
    r'releases/download/llvmorg-(\d+\.\d+\.\d+)/llvm-project-\1\.src\.tar\.xz'
)


def patch_text(text: str, expected_version: str) -> str:
    versions = VERSION_PATTERN.findall(text)
    if versions != [expected_version]:
        found = ", ".join(versions) if versions else "none"
        raise ValueError(
            f"expected exactly LLVM {expected_version}, found stable versions: {found}"
        )

    if text.count(PGO_ASSIGNMENT) != 1:
        raise ValueError(
            "expected exactly one known LLVM PGO assignment; formula has changed"
        )
    if SINGLE_STAGE_ASSIGNMENT in text:
        raise ValueError("LLVM formula is already patched for a single-stage build")
    if text.count("    lto_build = pgo_build && OS.mac?") != 1:
        raise ValueError("expected LLVM LTO assignment was not found exactly once")

    return text.replace(PGO_ASSIGNMENT, SINGLE_STAGE_ASSIGNMENT, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("formula", type=Path)
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()

    original = args.formula.read_text()
    patched = patch_text(original, args.expected_version)
    args.formula.write_text(patched)
    print(
        f"patched {args.formula}: LLVM {args.expected_version}, "
        "PGO disabled, LTO disabled"
    )


if __name__ == "__main__":
    main()
