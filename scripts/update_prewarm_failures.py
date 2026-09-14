#!/usr/bin/env python3
"""Update the optional prewarm quarantine from GitHub Actions job results."""

import argparse
import json
from pathlib import Path
from typing import Any

from plan_targets import REPO, read_list

FAILURES = REPO / "prewarm-failures.txt"
FAILED_CONCLUSIONS = {"failure", "timed_out"}


def jobs_from(payload: Any) -> list[dict[str, Any]]:
    """Accept one jobs API response or gh api --paginate --slurp output."""
    pages = payload if isinstance(payload, list) else [payload]
    jobs = []
    for page in pages:
        if isinstance(page, dict):
            jobs.extend(job for job in page.get("jobs", []) if isinstance(job, dict))
    return jobs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--jobs-json", type=Path, required=True)
    args = parser.parse_args()

    marker = f" / {args.stage} / "
    failed: set[str] = set()
    succeeded: set[str] = set()
    payload = json.loads(args.jobs_json.read_text())
    for job in jobs_from(payload):
        name = str(job.get("name") or "")
        if marker not in name:
            continue
        formula = name.rsplit(" / ", 1)[-1]
        conclusion = job.get("conclusion")
        if conclusion == "success":
            succeeded.add(formula)
        elif conclusion in FAILED_CONCLUSIONS:
            failed.add(formula)

    quarantined = set(read_list(FAILURES))
    quarantined.difference_update(succeeded)
    quarantined.update(failed)
    header = [
        "# Optional Formulae quarantined after a failed or timed-out prewarm job.",
        "# A successful manual warm-bottles retry removes the Formula automatically.",
        "",
    ]
    FAILURES.write_text("\n".join(header + sorted(quarantined)) + "\n")
    print(
        f"prewarm outcomes for {args.stage}: {len(succeeded)} succeeded, "
        f"{len(failed)} failed, {len(quarantined)} quarantined"
    )


if __name__ == "__main__":
    main()
