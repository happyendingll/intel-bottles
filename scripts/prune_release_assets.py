#!/usr/bin/env python3
"""Find and optionally delete Release bottles unused by active manifests.

The default mode is a read-only audit.  Deletion requires --delete and interactive
confirmation (or --yes).  Release objects themselves are never deleted.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse


PROJECT = Path(__file__).resolve().parent.parent
MANIFEST = PROJECT / "manifest"
MANAGED_TAG = re.compile(r"bottles(?:-warm-\d+)?$")


def run(command: list[str]) -> str:
    try:
        process = subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit(f"required command not found: {command[0]}")
    if process.returncode:
        detail = process.stderr.strip() or process.stdout.strip() or "unknown error"
        sys.exit(f"command failed: {' '.join(command)}\n{detail}")
    return process.stdout


def repository_from_remote() -> str | None:
    configured = os.environ.get("GITHUB_REPOSITORY")
    if configured:
        return configured
    remote = run(["git", "config", "--get", "remote.origin.url"]).strip()
    match = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", remote)
    return match.group(1) if match else None


def release_location(root_url: str) -> tuple[str, str] | None:
    parsed = urlparse(root_url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        return None
    parts = parsed.path.strip("/").split("/")
    if len(parts) != 5 or parts[2:4] != ["releases", "download"]:
        return None
    return f"{parts[0]}/{parts[1]}", unquote(parts[4])


def assets_from_manifests(
    paths: list[Path], repo: str
) -> dict[str, set[str]]:
    """Return Release asset names from the supplied manifests, grouped by tag."""
    references: dict[str, set[str]] = defaultdict(set)
    for path in paths:
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            sys.exit(f"cannot read active manifest {path}: {error}")
        if not isinstance(payload, dict):
            sys.exit(f"active manifest is not a JSON object: {path}")
        for formula in payload.values():
            bottle = formula.get("bottle") if isinstance(formula, dict) else None
            if not isinstance(bottle, dict):
                continue
            location = release_location(str(bottle.get("root_url") or ""))
            if not location or location[0].lower() != repo.lower():
                continue
            tag = location[1]
            tags = bottle.get("tags")
            if not isinstance(tags, dict) or not tags:
                sys.exit(f"missing bottle tags for {repo}@{tag} in {path}")
            for details in tags.values():
                filename = details.get("filename") if isinstance(details, dict) else None
                if not filename:
                    sys.exit(f"missing Release filename for {repo}@{tag} in {path}")
                # Homebrew stores the URL-facing name (for example llvm%4022), while
                # GitHub's assets API returns the decoded name (llvm@22).
                references[tag].add(unquote(str(filename)))
    return dict(references)


def active_assets(repo: str) -> tuple[dict[str, set[str]], int]:
    """Return active Release asset names grouped by tag and manifest count."""
    paths = sorted(MANIFEST.glob("*.bottle.json"))
    return assets_from_manifests(paths, repo), len(paths)


def gh_json(endpoint: str, paginate: bool = False) -> Any:
    command = ["gh", "api"]
    if paginate:
        command.extend(["--paginate", "--slurp"])
    command.append(endpoint)
    try:
        return json.loads(run(command))
    except json.JSONDecodeError as error:
        sys.exit(f"GitHub API returned invalid JSON for {endpoint}: {error}")


def flatten_pages(payload: Any, endpoint: str) -> list[dict[str, Any]]:
    pages = payload if isinstance(payload, list) else []
    flattened: list[dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, list):
            sys.exit(f"unexpected paginated response from {endpoint}")
        for item in page:
            if not isinstance(item, dict):
                sys.exit(f"unexpected item in response from {endpoint}")
            flattened.append(item)
    return flattened


def api_path(repo: str, suffix: str) -> str:
    return f"repos/{repo}/{suffix}" if suffix else f"repos/{repo}"


def format_size(size: int) -> str:
    value = float(size)
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    raise AssertionError("unreachable")


def verify_manifest_snapshot(repo: str) -> None:
    """Refuse to reason from manifests that differ from the remote default branch."""
    manifest_changes = run(["git", "status", "--porcelain", "--", str(MANIFEST)]).strip()
    if manifest_changes:
        sys.exit("manifest has local changes; commit and push them before auditing assets")

    repo_info = gh_json(api_path(repo, ""))
    default_branch = repo_info.get("default_branch") if isinstance(repo_info, dict) else None
    if not default_branch:
        sys.exit(f"cannot determine the default branch for {repo}")
    commit = gh_json(api_path(repo, f"commits/{quote(str(default_branch), safe='')}"))
    remote_head = commit.get("sha") if isinstance(commit, dict) else None
    local_head = run(["git", "rev-parse", "HEAD"]).strip()
    if not remote_head or local_head != remote_head:
        sys.exit(
            f"local HEAD is not {repo}:{default_branch}; pull the latest manifest commit first"
        )


def verify_no_active_workflows(repo: str) -> None:
    """Do not race a workflow that may be publishing assets and manifests."""
    for status in ("queued", "in_progress"):
        runs = gh_json(api_path(repo, f"actions/runs?status={status}&per_page=1"))
        count = runs.get("total_count") if isinstance(runs, dict) else None
        if not isinstance(count, int):
            sys.exit(f"cannot verify {status} Actions runs")
        if count:
            sys.exit(f"refusing deletion while {count} Actions run(s) are {status}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit or delete Release bottles unused by active manifests."
    )
    parser.add_argument("--repo", help="GitHub owner/repo (defaults to origin)")
    parser.add_argument(
        "--release",
        action="append",
        default=[],
        metavar="TAG",
        help="also inspect this tag even if it does not match bottles[-warm-N]",
    )
    parser.add_argument("--delete", action="store_true", help="delete orphan bottle assets")
    parser.add_argument("--yes", action="store_true", help="skip --delete confirmation")
    args = parser.parse_args()
    if args.yes and not args.delete:
        parser.error("--yes requires --delete")

    repo = args.repo or repository_from_remote()
    if not repo or repo.count("/") != 1:
        parser.error("cannot determine GitHub repository; pass --repo OWNER/REPO")

    verify_manifest_snapshot(repo)
    references, manifest_count = active_assets(repo)
    releases_endpoint = api_path(repo, "releases?per_page=100")
    releases = flatten_pages(gh_json(releases_endpoint, paginate=True), releases_endpoint)
    requested = set(args.release)
    selected = {
        str(release.get("tag_name")): release
        for release in releases
        if release.get("tag_name")
        and (
            MANAGED_TAG.fullmatch(str(release["tag_name"]))
            or str(release["tag_name"]) in references
            or str(release["tag_name"]) in requested
        )
    }
    missing_releases = (set(references) | requested) - set(selected)
    if missing_releases:
        sys.exit("Release tag(s) not found: " + ", ".join(sorted(missing_releases)))
    if not selected:
        sys.exit(f"no managed bottle Releases found in {repo}")

    print(f"repository: {repo}")
    print(f"active manifests: {manifest_count}")
    orphans: list[tuple[str, int, str, int]] = []
    missing_assets: list[tuple[str, str]] = []
    for tag, release in sorted(selected.items()):
        release_id = release.get("id")
        if not isinstance(release_id, int):
            sys.exit(f"Release {tag} has no numeric id")
        assets_endpoint = api_path(repo, f"releases/{release_id}/assets?per_page=100")
        assets = flatten_pages(gh_json(assets_endpoint, paginate=True), assets_endpoint)
        bottle_assets = {
            str(asset["name"]): asset
            for asset in assets
            if isinstance(asset.get("name"), str)
            and str(asset["name"]).endswith(".bottle.tar.gz")
        }
        live = references.get(tag, set())
        for filename in sorted(live - set(bottle_assets)):
            missing_assets.append((tag, filename))
        unused = sorted(set(bottle_assets) - live)
        unused_bytes = 0
        for filename in unused:
            asset = bottle_assets[filename]
            asset_id = asset.get("id")
            size = asset.get("size", 0)
            if not isinstance(asset_id, int) or not isinstance(size, int):
                sys.exit(f"Release asset has invalid id/size: {tag}/{filename}")
            unused_bytes += size
            orphans.append((tag, asset_id, filename, size))
        print(
            f"{tag}: {len(bottle_assets)} bottle assets, {len(live)} referenced, "
            f"{len(unused)} orphan ({format_size(unused_bytes)})"
        )
        for filename in unused:
            print(f"  orphan: {filename}")

    if missing_assets:
        print("\nERROR: active manifests reference missing Release assets:", file=sys.stderr)
        for tag, filename in missing_assets:
            print(f"  {tag}/{filename}", file=sys.stderr)
        sys.exit("refusing deletion because the active manifest set is inconsistent")

    total_bytes = sum(item[3] for item in orphans)
    action = "would delete" if not args.delete else "selected for deletion"
    print(f"\n{action}: {len(orphans)} assets ({format_size(total_bytes)})")
    if not args.delete or not orphans:
        return

    if not args.yes:
        if not sys.stdin.isatty():
            sys.exit("non-interactive deletion requires --yes")
        expected = f"DELETE {len(orphans)} ASSETS"
        answer = input(f"Type {expected!r} to continue: ")
        if answer != expected:
            sys.exit("deletion cancelled")

    # Repeat the snapshot check in case a workflow committed while the report was
    # being reviewed, then make sure no publisher is currently running.
    verify_manifest_snapshot(repo)
    verify_no_active_workflows(repo)

    deleted = 0
    for tag, asset_id, filename, _size in orphans:
        print(f"deleting {tag}/{filename}")
        run(["gh", "api", "--method", "DELETE", api_path(repo, f"releases/assets/{asset_id}")])
        deleted += 1
    print(f"deleted {deleted} orphan assets; Release objects were retained")


if __name__ == "__main__":
    main()
