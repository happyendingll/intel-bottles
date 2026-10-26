#!/usr/bin/env python3
"""Use the selected Xcode Swift instead of building Swift on Sequoia CI."""

from __future__ import annotations

import argparse
from pathlib import Path


OLD = 'uses_from_macos "swift" => :build, since: :tahoe'
NEW = 'uses_from_macos "swift" => :build'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("formula", type=Path)
    args = parser.parse_args()
    original = args.formula.read_text()
    if original.count(OLD) == 1:
        args.formula.write_text(original.replace(OLD, NEW, 1))
        print(f"patched {args.formula}: use selected Xcode Swift on Sequoia")
    elif original.count(NEW) == 1:
        print(f"already uses Xcode Swift on Sequoia: {args.formula}")
    else:
        raise ValueError("unexpected swift-protobuf Swift dependency; review upstream Formula")


if __name__ == "__main__":
    main()
