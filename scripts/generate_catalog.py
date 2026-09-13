#!/usr/bin/env python3
"""Generate a conservative optional-bottle catalog for macOS 15 Intel.

Popularity only determines ordering. A Formula is emitted only when it is compatible,
currently lacks a usable bottle on this runner, and is not blocked by the target,
exclude, heavyweight, or curated upstream-binary policies.
"""

import argparse
import json
import platform
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import brewinfo
from plan_targets import REPO, read_list

ANALYTICS_URL = "https://formulae.brew.sh/api/analytics/install-on-request/365d.json"
FORMULAE_URL = "https://formulae.brew.sh/api/formula.json"


def load_json(source: str) -> Any:
    path = Path(source)
    if path.exists():
        return json.loads(path.read_text())
    request = urllib.request.Request(source, headers={"User-Agent": "intel-bottles"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def analytics_names(payload: Any) -> list[str]:
    items = payload.get("items", []) if isinstance(payload, dict) else payload
    names = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("formula") or item.get("name")
        if name and "/" not in name:
            names.append(name)
    return list(dict.fromkeys(names))


def incompatible(formula: dict[str, Any]) -> str | None:
    if formula.get("disabled"):
        return "disabled"
    if formula.get("deprecated"):
        return "deprecated"
    if not formula.get("urls", {}).get("stable", {}).get("url"):
        return "no stable release"
    for requirement in formula.get("requirements") or []:
        name = requirement.get("name")
        version = str(requirement.get("version") or "")
        if name == "linux":
            return "Linux-only"
        if name == "arch" and version == "arm64":
            return "arm64-only"
        if name == "macos" and version.isdigit() and int(version) > 15:
            return f"requires macOS {version}"
        if name == "maximum_macos" and version.isdigit() and int(version) < 15:
            return f"supports at most macOS {version}"
    return None


def dependency_closure(name: str, formulae: dict[str, dict[str, Any]]) -> set[str]:
    seen: set[str] = set()
    pending = [name]
    while pending:
        current = pending.pop()
        formula = formulae.get(current, {})
        deps = (formula.get("dependencies") or []) + (formula.get("build_dependencies") or [])
        for dependency in deps:
            short = dependency.split("/")[-1]
            if short not in seen:
                seen.add(short)
                pending.append(short)
    seen.discard(name)
    return seen


def classify_in_batches(names: list[str], size: int = 100) -> tuple[set[str], set[str]]:
    needs: set[str] = set()
    missing: set[str] = set()
    for start in range(0, len(names), size):
        batch_needs, _bottled, batch_missing = brewinfo.classify(names[start : start + size])
        needs.update(batch_needs)
        missing.update(batch_missing)
    return needs, missing


def in_family(name: str, families: set[str]) -> bool:
    """Treat versioned Formulae such as node@24 as members of the node family."""
    return any(name == family or name.startswith(f"{family}@") for family in families)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analytics-json", default=ANALYTICS_URL)
    parser.add_argument("--formulae-json", default=FORMULAE_URL)
    parser.add_argument("--needs-bottle-file", help="Use a runner audit list instead of brew")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--scan-limit", type=int, default=1500)
    parser.add_argument("--output", type=Path, default=REPO / "catalog.txt")
    parser.add_argument("--write", action="store_true", help="Write --output; otherwise print")
    args = parser.parse_args()
    if args.limit < 1 or args.scan_limit < args.limit:
        parser.error("require 1 <= --limit <= --scan-limit")
    if not args.needs_bottle_file:
        macos_major = platform.mac_ver()[0].partition(".")[0]
        if sys.platform != "darwin" or platform.machine() != "x86_64" or macos_major != "15":
            sys.exit(
                "direct bottle classification requires macOS 15 x86_64; "
                "run on macos-15-intel or pass --needs-bottle-file"
            )

    analytics = analytics_names(load_json(args.analytics_json))[: args.scan_limit]
    formula_list = load_json(args.formulae_json)
    formulae = {item["name"]: item for item in formula_list if item.get("name")}
    policy = load_json(str(REPO / "catalog-policy.json"))
    policy_excluded = set(policy.get("exclude", {}))
    targets = set(read_list(REPO / "targets.txt"))
    excluded = set(read_list(REPO / "exclude.txt"))
    heavyweight_families = set(read_list(REPO / "heavy.txt")) | set(
        policy.get("heavy_formulae", {})
    )
    heavyweight = {name for name in formulae if in_family(name, heavyweight_families)}

    compatible = []
    rejected: dict[str, str] = {}
    for name in analytics:
        formula = formulae.get(name)
        reason = "not in homebrew-core" if formula is None else incompatible(formula)
        if name in targets:
            reason = "mandatory target"
        elif name in policy_excluded:
            reason = policy["exclude"][name]["category"]
        elif name in excluded:
            reason = "excluded"
        elif in_family(name, heavyweight_families):
            reason = "heavyweight"
        if reason:
            rejected[name] = reason
        else:
            compatible.append(name)

    if args.needs_bottle_file:
        needs = set(read_list(Path(args.needs_bottle_file)))
        missing: set[str] = set()
    else:
        needs, missing = classify_in_batches(compatible + sorted(heavyweight))

    costly_missing = heavyweight & needs
    selected = []
    for name in compatible:
        if name in missing or name not in needs:
            continue
        blockers = dependency_closure(name, formulae) & (excluded | policy_excluded | costly_missing)
        if blockers:
            rejected[name] = "blocked by " + ", ".join(sorted(blockers))
            continue
        selected.append(name)
        if len(selected) == args.limit:
            break

    generated = datetime.now(timezone.utc).date().isoformat()
    header = [
        "# Optional Formulae recommended for bounded bottle prewarming.",
        "#",
        f"# Generated {generated} from Homebrew 365-day install-on-request analytics.",
        "# Filters: targets, incompatible/retired Formulae, exclude.txt, missing heavy.txt",
        "# dependencies, and catalog-policy.json. Regenerate with the manual",
        "# 'generate prewarm catalog' workflow on macos-15-intel.",
        "",
    ]
    output = "\n".join(header + selected) + "\n"
    if args.write:
        args.output.write_text(output)
    else:
        print(output, end="")
    print(
        f"catalog generation: scanned {len(analytics)}, compatible {len(compatible)}, "
        f"recommended {len(selected)}, rejected {len(rejected)}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
