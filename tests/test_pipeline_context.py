import importlib.util
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pipeline_context.py"
SPEC = importlib.util.spec_from_file_location("pipeline_context", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def write_manifest(directory: Path, name: str, version: str) -> None:
    (directory / f"{name}--{version}.sequoia.bottle.json").write_text(
        json.dumps({f"homebrew/core/{name}": {"formula": {"pkg_version": version}}})
    )


class PipelineContextTests(unittest.TestCase):
    def test_create_and_stamp_preserve_the_pipeline_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifests = root / "manifest"
            manifests.mkdir()
            write_manifest(manifests, "go", "1.0")
            failures = root / "prewarm-failures.txt"
            failures.write_text("old-failure\n")
            targets = root / "targets.txt"
            targets.write_text("# generated\ngo\n")
            context_path = root / "context.json"

            MODULE.create_context(
                Namespace(
                    output=context_path,
                    manifest_dir=manifests,
                    failures_file=failures,
                    targets_file=targets,
                    stage="sync",
                    run_id="10",
                    run_url="https://example.test/runs/10",
                )
            )
            MODULE.stamp_context(
                Namespace(
                    context=context_path,
                    stage="build",
                    run_id="11",
                    run_url="https://example.test/runs/11",
                )
            )
            MODULE.conclude_context(
                Namespace(context=context_path, stage="build", conclusion="cancelled")
            )

            context = json.loads(context_path.read_text())
            self.assertEqual({"go": "1.0"}, context["baseline_manifests"])
            self.assertEqual(["old-failure"], context["baseline_prewarm_failures"])
            self.assertEqual(["go"], context["targets"])
            self.assertEqual("10", context["runs"]["sync"]["id"])
            self.assertEqual("11", context["runs"]["build"]["id"])
            self.assertEqual("cancelled", context["runs"]["build"]["conclusion"])

    def test_report_separates_updates_additions_pending_and_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifests = root / "manifest"
            manifests.mkdir()
            write_manifest(manifests, "go", "2.0")
            write_manifest(manifests, "new-tool", "1.0")
            write_manifest(manifests, "still-old", "1.0")
            failures = root / "prewarm-failures.txt"
            failures.write_text("old-failure\nnew-failure\n")
            context = root / "context.json"
            context.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "baseline_manifests": {"go": "1.0", "still-old": "1.0"},
                        "baseline_prewarm_failures": ["old-failure"],
                        "targets": ["go", "still-old"],
                        "runs": {},
                    }
                )
            )
            output = root / "report.md"

            MODULE.render_report(
                Namespace(
                    context=context,
                    manifest_dir=manifests,
                    failures_file=failures,
                    output=output,
                    warm_results="wave0=success,wave1=cancelled,wave2=skipped",
                )
            )
            report = output.read_text()
            self.assertIn("`go`：`1.0` → `2.0`", report)
            self.assertIn("`new-tool`：`1.0`", report)
            self.assertIn("`still-old`（当前 manifest：`1.0`）", report)
            self.assertIn("`new-failure`", report)
            self.assertIn("| 当前有效 manifest 总数 | 3 |", report)
            self.assertIn("部分环节失败或取消", report)
            self.assertIn("| `wave1` | `cancelled` |", report)
            self.assertIn("`warm wave1`：`cancelled`", report)


if __name__ == "__main__":
    unittest.main()
