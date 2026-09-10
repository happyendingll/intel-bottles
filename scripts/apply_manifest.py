#!/usr/bin/env python3
"""Plan how to rebuild the fork as upstream plus matching bottle blocks.

The fork is never hand-edited. It is rebuilt from upstream and this plan is replayed,
so merge conflicts are structurally impossible.

VERSION REFRESH: when upstream bumps a formula past the version in the manifest, its stale
bottle block is deliberately not re-applied. The upstream formula therefore remains in the
fork without our bottle and is picked up by the following build-bottles plan. A successful
build writes the new bottle block back to the fork.

Emits one tab-separated instruction per still-current manifest on stdout:
    APPLY <json_path>
"""

import json
import sys
from pathlib import Path

import brewinfo

MANIFEST = Path(__file__).resolve().parent.parent / "manifest"


def main() -> None:
    entries = []
    for path in sorted(MANIFEST.glob("*.bottle.json")):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            print(f"skipping unreadable {path.name}", file=sys.stderr)
            continue
        for full_name, payload in data.items():
            formula = payload.get("formula") or {}
            entries.append(
                {
                    "json": path,
                    "name": full_name.split("/")[-1],
                    "version": formula.get("pkg_version"),
                    "revision": formula.get("tap_git_revision"),
                    "path": formula.get("tap_git_path"),
                }
            )

    if not entries:
        print("manifest is empty", file=sys.stderr)
        return

    upstream = brewinfo.pkg_versions(sorted({e["name"] for e in entries}))

    current, held, dropped = [], [], []
    for entry in entries:
        now = upstream.get(entry["name"])
        if now is None:
            dropped.append((entry["name"], "no longer in homebrew-core"))
        elif now == entry["version"]:
            current.append(entry)
        elif entry["revision"] and entry["path"]:
            held.append((entry, now))
        else:
            dropped.append((entry["name"], "bottled before revisions were recorded"))

    # A held entry describes a stale manifest. Do not restore its old formula and do not
    # re-apply its old bottle: leaving upstream's version in the fork is what makes the
    # next build plan see that a new bottle is required.
    for entry in current:
        print(f"APPLY\t{entry['json']}")

    print(
        f"\n{len(current)} at upstream version, {len(held)} held back, {len(dropped)} dropped",
        file=sys.stderr,
    )
    for entry, now in held:
        print(
            f"  hold: {entry['name']} stays at {entry['version']} (upstream {now}) "
            f"until CI bottles it",
            file=sys.stderr,
        )
    for name, why in dropped:
        print(f"  drop: {name} -- {why}", file=sys.stderr)


if __name__ == "__main__":
    main()
