#!/usr/bin/env python3
"""Delete bottle assets belonging to manifests replaced by a successful build.

This is intentionally narrower than prune_release_assets.py: CI supplies only the old
manifests replaced in the current publish job.  Every candidate is checked against the
post-push active manifest set before its Release asset is removed.
"""

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import quote

from prune_release_assets import (
    active_assets,
    api_path,
    assets_from_manifests,
    flatten_pages,
    gh_json,
    repository_from_remote,
    run,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--repo", help="GitHub owner/repo (defaults to GITHUB_REPOSITORY)")
    args = parser.parse_args()

    repo = args.repo or os.environ.get("GITHUB_REPOSITORY") or repository_from_remote()
    if not repo or repo.count("/") != 1:
        parser.error("cannot determine GitHub repository; pass --repo OWNER/REPO")

    paths = sorted(args.candidates.glob("*.bottle.json"))
    if not paths:
        print("no replaced manifests; nothing to delete")
        return

    candidates = assets_from_manifests(paths, repo)
    active, manifest_count = active_assets(repo)
    obsolete = {
        tag: names - active.get(tag, set()) for tag, names in candidates.items()
    }
    obsolete = {tag: names for tag, names in obsolete.items() if names}
    retained = sum(len(names & active.get(tag, set())) for tag, names in candidates.items())
    print(
        f"checked {len(paths)} replaced manifests against {manifest_count} active: "
        f"{sum(map(len, obsolete.values()))} obsolete, {retained} still referenced"
    )

    # Resolve every candidate before mutating GitHub.  An API or schema failure therefore
    # cannot leave a partially validated deletion plan.
    deletions: list[tuple[str, int, str]] = []
    for tag, names in sorted(obsolete.items()):
        release = gh_json(api_path(repo, f"releases/tags/{quote(tag, safe='')}"))
        release_id = release.get("id") if isinstance(release, dict) else None
        if not isinstance(release_id, int):
            sys.exit(f"Release {tag} has no numeric id")
        endpoint = api_path(repo, f"releases/{release_id}/assets?per_page=100")
        assets = flatten_pages(gh_json(endpoint, paginate=True), endpoint)
        by_name = {
            str(asset["name"]): asset
            for asset in assets
            if isinstance(asset.get("name"), str)
        }
        for name in sorted(names):
            asset = by_name.get(name)
            if asset is None:
                print(f"already absent: {tag}/{name}")
                continue
            asset_id = asset.get("id")
            if not isinstance(asset_id, int):
                sys.exit(f"Release asset has no numeric id: {tag}/{name}")
            deletions.append((tag, asset_id, name))

    for tag, asset_id, name in deletions:
        print(f"deleting replaced bottle: {tag}/{name}")
        run(["gh", "api", "--method", "DELETE", api_path(repo, f"releases/assets/{asset_id}")])
    print(f"deleted {len(deletions)} replaced bottle assets")


if __name__ == "__main__":
    main()
