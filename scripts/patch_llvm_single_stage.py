#!/usr/bin/env python3
"""Disable Homebrew's multi-stage PGO build for any unversioned LLVM release.

The known PGO/LTO control lines are still checked strictly. If Homebrew changes
their structure, fail before building rather than silently running the PGO path.
"""

from __future__ import annotations

import argparse
from pathlib import Path


PGO_ASSIGNMENT = (
    "    pgo_build = build.stable? && build.bottle? && OS.mac? && !versioned_formula?"
)
SINGLE_STAGE_ASSIGNMENT = (
    "    pgo_build = false # Intel CI: build this bottle in one stage"
)


def patch_text(text: str) -> str:
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
    args = parser.parse_args()

    original = args.formula.read_text()
    patched = patch_text(original)
    args.formula.write_text(patched)
    print(f"patched {args.formula}: PGO disabled, LTO disabled")


if __name__ == "__main__":
    main()
