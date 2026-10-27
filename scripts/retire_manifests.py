#!/usr/bin/env python3
"""Stage DROP manifests for asset cleanup, then remove them from the active set."""

import argparse
import shutil
from pathlib import Path


MANIFEST = Path(__file__).resolve().parent.parent / "manifest"


def drop_paths(plan: Path, manifest_dir: Path) -> list[Path]:
    root = manifest_dir.resolve()
    paths = []
    for line in plan.read_text().splitlines():
        if not line.startswith("DROP\t"):
            continue
        fields = line.split("\t")
        if len(fields) != 3:
            raise ValueError(f"invalid DROP instruction: {line}")
        path = Path(fields[1]).resolve()
        if path.parent != root or not path.name.endswith(".bottle.json"):
            raise ValueError(f"DROP path is not an active manifest: {path}")
        if not path.is_file():
            raise ValueError(f"DROP manifest is missing: {path}")
        paths.append(path)
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate DROP manifest")
    return paths


def retire(plan: Path, candidates: Path, manifest_dir: Path = MANIFEST) -> int:
    paths = drop_paths(plan, manifest_dir)
    candidates.mkdir(parents=True, exist_ok=True)
    for path in paths:
        shutil.copy2(path, candidates / path.name)
    for path in paths:
        path.unlink()
        print(f"retired {path.name}")
    print(f"retired {len(paths)} manifest(s)")
    return len(paths)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--candidates", required=True, type=Path)
    args = parser.parse_args()
    retire(args.plan, args.candidates)


if __name__ == "__main__":
    main()
