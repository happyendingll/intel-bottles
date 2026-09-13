#!/usr/bin/env python3
"""Select a bounded daily batch of optional Formulae for bottle prewarming.

The mandatory targets are handled by build-bottles.yml first. This planner runs against
the resulting fork, removes anything that already has a usable bottle, and schedules at
most WARM_LIMIT optional roots. Daily hash ordering prevents a repeatedly failing formula
from permanently blocking the rest of the catalog without requiring persistent state.
"""

import hashlib
import os
import sys
from datetime import datetime, timezone

import brewinfo
from plan_targets import REPO, emit, levels, read_list

WARM_TIMEOUT_MINUTES = 60


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def dependencies(formulae: list[str]) -> dict[str, set[str]]:
    """Return each formula's complete build dependency set."""
    if not formulae:
        return {}

    from plan_targets import brew

    output = brew("deps", "--include-build", "--full-name", "--for-each", *formulae)
    result = {name: set() for name in formulae}
    for line in output.splitlines():
        if ":" not in line:
            continue
        name, _, rest = line.partition(":")
        short = name.strip().split("/")[-1]
        if short in result:
            result[short] = {item.split("/")[-1] for item in rest.split()}
    return result


def main() -> None:
    try:
        limit = int(os.environ.get("WARM_LIMIT", "100"))
    except ValueError:
        sys.exit("WARM_LIMIT must be an integer")
    if not 1 <= limit <= 100:
        sys.exit("WARM_LIMIT must be between 1 and 100")

    override = os.environ.get("OVERRIDE", "").split()
    catalog = unique(override or read_list(REPO / "catalog.txt"))
    targets = set(read_list(REPO / "targets.txt"))
    excluded = set(read_list(REPO / "exclude.txt"))
    candidates = [name for name in catalog if name not in targets and name not in excluded]

    needs, bottled, missing = brewinfo.classify(candidates)
    if missing:
        print(f"note: no longer in homebrew-core: {', '.join(sorted(missing))}", file=sys.stderr)
    print(
        f"catalog: {len(candidates)} candidates, {len(bottled)} already bottled, "
        f"{len(needs)} need a bottle"
    )
    if not needs:
        emit({}, [], timeout_cap=WARM_TIMEOUT_MINUTES)
        return

    all_deps = dependencies(needs)
    blocked = {name for name in needs if all_deps.get(name, set()) & excluded}
    if blocked:
        print(
            "note: blocked by exclude.txt: " + ", ".join(sorted(blocked)),
            file=sys.stderr,
        )
    buildable = [name for name in needs if name not in blocked]

    if override:
        ranked = buildable
        seed = "manual override"
    else:
        seed = os.environ.get("WARM_SEED") or datetime.now(timezone.utc).date().isoformat()
        ranked = sorted(
            buildable,
            key=lambda name: hashlib.sha256(f"{seed}\0{name}".encode()).digest(),
        )
    selected = ranked[:limit]
    print(f"prewarm selection ({seed}, limit {limit}): {', '.join(selected) or 'none'}")

    # Preserve dependency ordering when two selected roots depend on one another. Any
    # unselected dependency is built inside its root job and is published with that root.
    selected_set = set(selected)
    selected_deps = {
        name: all_deps.get(name, set()) & selected_set for name in selected
    }
    depth = levels(selected_deps)
    waves: dict[int, list[str]] = {}
    for name in selected:
        waves.setdefault(depth.get(name, 0), []).append(name)
    emit(waves, selected, timeout_cap=WARM_TIMEOUT_MINUTES)


if __name__ == "__main__":
    main()
