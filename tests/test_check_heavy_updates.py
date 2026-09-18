import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_heavy_updates.py"
SPEC = importlib.util.spec_from_file_location("check_heavy_updates", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class HeavyUpdateCheckTests(unittest.TestCase):
    def test_compares_pkg_version_and_ignores_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest"
            manifest.mkdir()
            (manifest / "go--1.2_1.sequoia.bottle.json").write_text(
                json.dumps({"homebrew/core/go": {"formula": {"pkg_version": "1.2_1"}}})
            )
            archive = manifest / "archive"
            archive.mkdir()
            (archive / "rust--old.sequoia.bottle.json").write_text(
                json.dumps({"homebrew/core/rust": {"formula": {"pkg_version": "9.9"}}})
            )

            payloads = {
                "go": {
                    "versions": {"stable": "1.2"},
                    "revision": 1,
                    "bottle": {"stable": {"files": {"arm64_sequoia": {}, "sequoia": {}}}},
                },
                "rust": {
                    "versions": {"stable": "2.0"},
                    "revision": 0,
                    "bottle": {"stable": {"files": {"x86_64_linux": {}}}},
                },
            }
            with patch.object(MODULE, "fetch_formula", side_effect=lambda name, _: payloads[name]):
                report = MODULE.build_report(["go", "rust"], manifest)

            self.assertEqual("current", report["formulae"][0]["status"])
            self.assertEqual(["sequoia"], report["formulae"][0]["official_intel_macos_tags"])
            self.assertEqual("missing", report["formulae"][1]["status"])
            self.assertEqual(1, report["needs_attention"])


if __name__ == "__main__":
    unittest.main()
