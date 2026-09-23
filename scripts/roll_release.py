#!/usr/bin/env python3
"""Choose a rolling Release for one verified publish batch and retarget its JSON."""

import argparse
import json
import re
import sys
from pathlib import Path

from prune_release_assets import api_path, flatten_pages, gh_json


MAX_ASSETS = 900  # Leave room below GitHub's 1,000-assets-per-Release limit.


def release_number(tag: str, base: str) -> int | None:
    if base == "bottles":
        if tag == base:
            return 1
        match = re.fullmatch(r"bottles-(\d+)", tag)
        return int(match.group(1)) if match and int(match.group(1)) >= 2 else None

    match = re.fullmatch(r"bottles-warm-(\d+)", base)
    if not match:
        raise ValueError(f"unsupported rolling Release base: {base}")
    number = re.fullmatch(r"bottles-warm-(\d+)", tag)
    return int(number.group(1)) if number and int(number.group(1)) >= int(match.group(1)) else None


def next_tag(base: str, number: int) -> str:
    return f"bottles-{number + 1}" if base == "bottles" else f"bottles-warm-{number + 1}"


def choose_tag(
    base: str,
    releases: list[dict],
    existing_assets: set[str],
    batch_assets: set[str],
    max_assets: int = MAX_ASSETS,
) -> str:
    if len(batch_assets) > max_assets:
        raise ValueError(f"publish batch has {len(batch_assets)} assets; limit is {max_assets}")
    numbered = [
        (number, release["tag_name"])
        for release in releases
        if isinstance(release.get("tag_name"), str)
        and (number := release_number(release["tag_name"], base)) is not None
    ]
    if not numbered:
        return base
    number, current = max(numbered)
    if len(existing_assets | batch_assets) <= max_assets:
        return current
    return next_tag(base, number)


def retarget_json(paths: list[Path], old_url: str, new_url: str) -> None:
    # Validate the complete batch before changing any file.
    changes: list[tuple[Path, dict]] = []
    for path in paths:
        payload = json.loads(path.read_text())
        if not isinstance(payload, dict) or len(payload) != 1:
            raise ValueError(f"unexpected bottle JSON structure: {path}")
        formula = next(iter(payload.values()))
        bottle = formula.get("bottle") if isinstance(formula, dict) else None
        if not isinstance(bottle, dict) or bottle.get("root_url") != old_url:
            raise ValueError(f"unexpected bottle root_url in {path}")
        bottle["root_url"] = new_url
        changes.append((path, payload))
    for path, payload in changes:
        path.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base-tag", required=True)
    parser.add_argument("--staging", required=True, type=Path)
    args = parser.parse_args()

    jsons = sorted(args.staging.glob("*.bottle.json"))
    # Homebrew writes a double dash; publish.sh uploads the URL-facing single dash.
    assets = {
        path.name.replace("--", "-", 1)
        for path in args.staging.glob("*.bottle.tar.gz")
    }
    if not jsons or not assets:
        parser.error("staging must contain verified bottle JSON and tarballs")

    endpoint = api_path(args.repo, "releases?per_page=100")
    releases = flatten_pages(gh_json(endpoint, paginate=True), endpoint)
    numbered = [
        (number, release)
        for release in releases
        if isinstance(release.get("tag_name"), str)
        and (number := release_number(release["tag_name"], args.base_tag)) is not None
    ]
    existing: set[str] = set()
    if numbered:
        current = max(numbered, key=lambda item: item[0])[1]
        release_id = current.get("id")
        if not isinstance(release_id, int):
            parser.error(f"Release {current['tag_name']} has no numeric id")
        assets_endpoint = api_path(args.repo, f"releases/{release_id}/assets?per_page=100")
        existing = {
            asset["name"]
            for asset in flatten_pages(gh_json(assets_endpoint, paginate=True), assets_endpoint)
            if isinstance(asset.get("name"), str)
        }

    try:
        selected = choose_tag(args.base_tag, releases, existing, assets)
        old_url = f"https://github.com/{args.repo}/releases/download/{args.base_tag}"
        new_url = f"https://github.com/{args.repo}/releases/download/{selected}"
        retarget_json(jsons, old_url, new_url)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(
        f"Release {selected}: {len(existing)} existing asset(s), "
        f"{len(assets)} in this batch (safe cap {MAX_ASSETS})",
        file=sys.stderr,
    )
    print(selected)


if __name__ == "__main__":
    main()
