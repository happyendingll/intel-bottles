#!/usr/bin/env python3
"""Carry a bottle-pipeline baseline across workflows and render its final report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


REPO = Path(__file__).resolve().parent.parent


def read_list(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def manifest_versions(manifest_dir: Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    # Active manifests live directly under manifest/. Never include archive/.
    for path in sorted(manifest_dir.glob("*.bottle.json")):
        data = json.loads(path.read_text())
        for full_name, payload in data.items():
            name = full_name.split("/")[-1]
            version = (payload.get("formula") or {}).get("pkg_version")
            if version:
                versions[name] = str(version)
    return versions


def run_entry(run_id: str, run_url: str) -> dict[str, str]:
    return {"id": str(run_id), "url": run_url}


def create_context(args: argparse.Namespace) -> None:
    context = {
        "schema": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "baseline_manifests": manifest_versions(args.manifest_dir),
        "baseline_prewarm_failures": sorted(read_list(args.failures_file)),
        "targets": sorted(read_list(args.targets_file)),
        "runs": {args.stage: run_entry(args.run_id, args.run_url)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(context, indent=2, sort_keys=True) + "\n")


def stamp_context(args: argparse.Namespace) -> None:
    context = json.loads(args.context.read_text())
    if context.get("schema") != 1:
        raise SystemExit(f"unsupported pipeline context schema in {args.context}")
    context.setdefault("runs", {})[args.stage] = run_entry(args.run_id, args.run_url)
    args.context.write_text(json.dumps(context, indent=2, sort_keys=True) + "\n")


def conclude_context(args: argparse.Namespace) -> None:
    context = json.loads(args.context.read_text())
    if context.get("schema") != 1:
        raise SystemExit(f"unsupported pipeline context schema in {args.context}")
    entry = context.setdefault("runs", {}).setdefault(args.stage, {})
    entry["conclusion"] = args.conclusion
    args.context.write_text(json.dumps(context, indent=2, sort_keys=True) + "\n")


def bullets(items: list[str], empty: str) -> list[str]:
    return [f"- {item}" for item in items] if items else [f"- {empty}"]


def render_report(args: argparse.Namespace) -> None:
    context: dict[str, Any] = json.loads(args.context.read_text())
    baseline = {
        str(name): str(version)
        for name, version in context.get("baseline_manifests", {}).items()
    }
    final = manifest_versions(args.manifest_dir)
    targets = set(map(str, context.get("targets", [])))

    updated = [
        f"`{name}`：`{baseline[name]}` → `{final[name]}`"
        for name in sorted(baseline.keys() & final.keys())
        if baseline[name] != final[name]
    ]
    added = [
        f"`{name}`：`{final[name]}`"
        for name in sorted(final.keys() - baseline.keys())
    ]
    pending = [
        f"`{name}`（当前 manifest：`{final.get(name, '缺失')}`）"
        for name in sorted(targets)
        if final.get(name) == baseline.get(name)
    ]
    baseline_failures = set(map(str, context.get("baseline_prewarm_failures", [])))
    final_failures = set(read_list(args.failures_file))
    new_failures = [f"`{name}`" for name in sorted(final_failures - baseline_failures)]

    runs = context.get("runs", {})
    run_labels = [
        ("sync fork", "sync"),
        ("build bottles", "build"),
        ("generate catalog", "catalog"),
        ("warm bottles", "warm"),
    ]
    run_links = []
    run_conclusions = []
    for label, key in run_labels:
        entry = runs.get(key) or {}
        if entry.get("url"):
            conclusion = entry.get("conclusion")
            suffix = f" · {conclusion}" if conclusion else ""
            run_links.append(f"[{label}]({entry['url']}){suffix}")
        if entry.get("conclusion"):
            run_conclusions.append(str(entry["conclusion"]))

    warm_results = {}
    for item in args.warm_results.split(",") if args.warm_results else []:
        name, separator, result = item.partition("=")
        if separator and name and result:
            warm_results[name] = result
    degraded = any(result not in {"success", "skipped"} for result in warm_results.values())
    degraded = degraded or any(result != "success" for result in run_conclusions)
    pipeline_status = "已完成汇总（部分环节失败或取消，详见下表）" if degraded else "已完成"
    review_items = []
    for label, key in run_labels:
        conclusion = (runs.get(key) or {}).get("conclusion")
        if conclusion and conclusion != "success":
            review_items.append(f"`{label}`：`{conclusion}`")
    for name, result in warm_results.items():
        if result not in {"success", "skipped"}:
            review_items.append(f"`warm {name}`：`{result}`")

    report_date = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    lines = [
        f"## Intel bottle 闭环报告 · {report_date}",
        "",
        f"**链路状态：{pipeline_status}**",
        "",
        f"链路：{' → '.join(run_links) if run_links else '无运行链接'}",
        "",
        "| 项目 | 数量 |",
        "|---|---:|",
        f"| 已维护 Formula 版本更新成功 | {len(updated)} |",
        f"| 新增到维护集合 | {len(added)} |",
        f"| targets 中仍待更新 | {len(pending)} |",
        f"| 本轮新增预热失败/超时 | {len(new_failures)} |",
        f"| 当前有效 manifest 总数 | {len(final)} |",
        "",
        "### Warm wave 状态",
        "",
        "| Wave | 结果 |",
        "|---|---|",
        *(
            [f"| `{name}` | `{result}` |" for name, result in warm_results.items()]
            if warm_results
            else ["| - | 未提供（手动报告） |"]
        ),
        "",
        "### 需要人工复查",
        "",
        *bullets(review_items, "本轮没有失败或取消的链路环节。"),
        "",
        "### 已更新 Formula",
        "",
        *bullets(updated, "本轮没有已维护 Formula 完成版本替换。"),
        "",
        "### 新增 Formula",
        "",
        *bullets(added, "本轮没有新增 Formula 进入维护集合。"),
        "",
        "### 仍待更新",
        "",
        *bullets(pending, "targets 中没有遗留的旧版本 manifest。"),
        "",
        "### 新增失败或超时",
        "",
        *bullets(new_failures, "本轮没有新增预热隔离项。"),
        "",
        "_报告通过链路开始时的 manifest 快照与 warm 完成后的 main 分支比较生成。_",
        "",
    ]
    args.output.write_text("\n".join(lines))
    print("\n".join(lines))


def add_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--stage", required=True, choices=["sync", "build", "catalog", "warm"])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-url", required=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--manifest-dir", type=Path, default=REPO / "manifest")
    create.add_argument("--failures-file", type=Path, default=REPO / "prewarm-failures.txt")
    create.add_argument("--targets-file", type=Path, default=REPO / "targets.txt")
    add_run_arguments(create)
    create.set_defaults(func=create_context)

    stamp = subparsers.add_parser("stamp")
    stamp.add_argument("context", type=Path)
    add_run_arguments(stamp)
    stamp.set_defaults(func=stamp_context)

    conclude = subparsers.add_parser("conclude")
    conclude.add_argument("context", type=Path)
    conclude.add_argument("--stage", required=True, choices=["sync", "build", "catalog", "warm"])
    conclude.add_argument("--conclusion", required=True)
    conclude.set_defaults(func=conclude_context)

    report = subparsers.add_parser("report")
    report.add_argument("context", type=Path)
    report.add_argument("--output", type=Path, required=True)
    report.add_argument("--manifest-dir", type=Path, default=REPO / "manifest")
    report.add_argument("--failures-file", type=Path, default=REPO / "prewarm-failures.txt")
    report.add_argument("--warm-results", default="")
    report.set_defaults(func=render_report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
