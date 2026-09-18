#!/usr/bin/env python3
"""Compare heavy Formula versions with the active Intel bottle manifests."""

from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_API = "https://formulae.brew.sh/api/formula"


def read_formulae(path: Path) -> list[str]:
    names = []
    for raw in path.read_text().splitlines():
        name = raw.strip()
        if name and not name.startswith("#"):
            names.append(name)
    if not names:
        raise ValueError(f"no Formulae found in {path}")
    if len(names) != len(set(names)):
        raise ValueError(f"duplicate Formula names in {path}")
    return names


def active_manifest_versions(manifest_dir: Path) -> dict[str, set[str]]:
    versions: dict[str, set[str]] = {}
    # Deliberately do not recurse into manifest/archive.
    for path in sorted(manifest_dir.glob("*.bottle.json")):
        data = json.loads(path.read_text())
        for full_name, payload in data.items():
            name = full_name.split("/")[-1]
            version = (payload.get("formula") or {}).get("pkg_version")
            if version:
                versions.setdefault(name, set()).add(str(version))
    return versions


def fetch_formula(name: str, api_base: str) -> dict[str, Any]:
    encoded = urllib.parse.quote(name, safe="@")
    request = urllib.request.Request(
        f"{api_base.rstrip('/')}/{encoded}.json",
        headers={"User-Agent": "intel-bottles-heavy-update-check/1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def pkg_version(data: dict[str, Any]) -> str:
    version = str(data["versions"]["stable"])
    revision = int(data.get("revision") or 0)
    return f"{version}_{revision}" if revision else version


def intel_macos_tags(data: dict[str, Any]) -> list[str]:
    files = (((data.get("bottle") or {}).get("stable") or {}).get("files") or {})
    return sorted(
        tag
        for tag in files
        if not tag.startswith("arm64_") and not tag.endswith("_linux")
    )


def build_report(
    names: list[str], manifest_dir: Path, api_base: str = DEFAULT_API
) -> dict[str, Any]:
    manifests = active_manifest_versions(manifest_dir)
    rows = []
    for name in names:
        data = fetch_formula(name, api_base)
        upstream = pkg_version(data)
        local = sorted(manifests.get(name, set()))
        if upstream in local:
            status = "current"
        elif local:
            status = "outdated"
        else:
            status = "missing"
        rows.append(
            {
                "name": name,
                "upstream_version": upstream,
                "manifest_versions": local,
                "status": status,
                "official_intel_macos_tags": intel_macos_tags(data),
                "homepage": data.get("homepage") or "",
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "needs_attention": sum(row["status"] != "current" for row in rows),
        "formulae": rows,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "## Heavy Intel bottle update check",
        "",
        "| Formula | Official version | Active manifest | Status | Official Intel macOS bottle |",
        "|---|---:|---:|---|---|",
    ]
    labels = {"current": "current", "outdated": "needs rebuild", "missing": "missing"}
    for row in report["formulae"]:
        local = ", ".join(row["manifest_versions"]) or "—"
        tags = ", ".join(row["official_intel_macos_tags"]) or "none"
        lines.append(
            f"| `{row['name']}` | `{row['upstream_version']}` | `{local}` | "
            f"{labels[row['status']]} | {tags} |"
        )
    lines.extend(
        [
            "",
            f"Formulae needing attention: **{report['needs_attention']}**",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formulae", type=Path, default=Path("heavy-formulae.txt"))
    parser.add_argument("--manifest-dir", type=Path, default=Path("manifest"))
    parser.add_argument("--api-base", default=DEFAULT_API)
    parser.add_argument("--output", type=Path, default=Path("heavy-update-report.json"))
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()

    report = build_report(read_formulae(args.formulae), args.manifest_dir, args.api_base)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    rendered = markdown(report)
    if args.summary:
        with args.summary.open("a") as handle:
            handle.write(rendered)
    print(rendered)


if __name__ == "__main__":
    main()
