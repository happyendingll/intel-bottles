import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("apply_manifest", SCRIPTS / "apply_manifest.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class ApplyManifestTests(unittest.TestCase):
    def test_removed_upstream_formula_is_not_sent_to_bottle_merge(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest"
            manifest.mkdir()
            core = root / "homebrew-core"
            formula_dir = core / "Formula" / "o"
            formula_dir.mkdir(parents=True)
            (formula_dir / "openssl@3.rb").write_text("class OpensslAT3 < Formula; end\n")

            for name, version in (("openssl@3", "3.6.5"), ("openssl@3.5", "3.5.9")):
                (manifest / f"{name}--{version}.sequoia.bottle.json").write_text(
                    json.dumps(
                        {
                            name: {
                                "formula": {
                                    "pkg_version": version,
                                    "tap_git_path": f"Formula/o/{name}.rb",
                                    "tap_git_revision": "abc123",
                                }
                            }
                        }
                    )
                )

            output = io.StringIO()
            errors = io.StringIO()
            with (
                patch.object(MODULE, "MANIFEST", manifest),
                patch.object(MODULE.subprocess, "check_output", return_value=str(core)),
                patch.object(
                    MODULE.brewinfo,
                    "pkg_versions",
                    return_value={"openssl@3": "3.6.5", "openssl@3.5": "3.5.9"},
                ) as versions,
                contextlib.redirect_stdout(output),
                contextlib.redirect_stderr(errors),
            ):
                MODULE.main()

            versions.assert_called_once_with(["openssl@3"])
            self.assertIn("openssl@3--3.6.5.sequoia.bottle.json", output.getvalue())
            self.assertNotIn("APPLY\t" + str(manifest / "openssl@3.5--3.5.9.sequoia.bottle.json"), output.getvalue())
            self.assertIn("DROP\t", output.getvalue())
            self.assertIn("drop: openssl@3.5 -- no longer in homebrew-core", errors.getvalue())

    def test_stale_manifest_is_dropped_only_when_upstream_has_all_bottle(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest"
            manifest.mkdir()
            core = root / "homebrew-core"
            for name in ("portable", "needs-build"):
                formula = core / "Formula" / name[0] / f"{name}.rb"
                formula.parent.mkdir(parents=True, exist_ok=True)
                formula.write_text("class Example < Formula; end\n")
                (manifest / f"{name}--1.0.sequoia.bottle.json").write_text(
                    json.dumps(
                        {
                            name: {
                                "formula": {
                                    "pkg_version": "1.0",
                                    "tap_git_path": f"Formula/{name[0]}/{name}.rb",
                                    "tap_git_revision": "abc123",
                                }
                            }
                        }
                    )
                )

            output = io.StringIO()
            with (
                patch.object(MODULE, "MANIFEST", manifest),
                patch.object(MODULE.subprocess, "check_output", return_value=str(core)),
                patch.object(
                    MODULE.brewinfo, "pkg_versions",
                    return_value={"portable": "2.0", "needs-build": "2.0"},
                ),
                patch.object(MODULE.brewinfo, "all_bottles", return_value={"portable"}),
                contextlib.redirect_stdout(output),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                MODULE.main()

            plan = output.getvalue()
            self.assertIn(f"DROP\t{manifest / 'portable--1.0.sequoia.bottle.json'}", plan)
            self.assertIn("HELD\tneeds-build", plan)
            self.assertNotIn("HELD\tportable", plan)

    def test_incomplete_core_checkout_cannot_drop_every_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest"
            manifest.mkdir()
            for name in ("a", "b", "c"):
                (manifest / f"{name}--1.0.sequoia.bottle.json").write_text(
                    json.dumps(
                        {
                            name: {
                                "formula": {
                                    "pkg_version": "1.0",
                                    "tap_git_path": f"Formula/{name}/{name}.rb",
                                    "tap_git_revision": "abc123",
                                }
                            }
                        }
                    )
                )
            with (
                patch.object(MODULE, "MANIFEST", manifest),
                patch.object(MODULE.subprocess, "check_output", return_value=str(root / "empty-core")),
                self.assertRaisesRegex(SystemExit, "incomplete core checkout"),
            ):
                MODULE.main()


if __name__ == "__main__":
    unittest.main()
