import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "retire_manifests.py"
SPEC = importlib.util.spec_from_file_location("retire_manifests", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class RetireManifestsTests(unittest.TestCase):
    def test_stages_only_drop_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest"
            manifest.mkdir()
            dropped = manifest / "old--1.0.sequoia.bottle.json"
            kept = manifest / "kept--1.0.sequoia.bottle.json"
            dropped.write_text("old bottle")
            kept.write_text("kept bottle")
            plan = root / "plan.tsv"
            plan.write_text(f"APPLY\t{kept}\nDROP\t{dropped}\tupstream has an all bottle\n")
            candidates = root / "candidates"

            self.assertEqual(1, MODULE.retire(plan, candidates, manifest))
            self.assertFalse(dropped.exists())
            self.assertTrue(kept.exists())
            self.assertEqual("old bottle", (candidates / dropped.name).read_text())

    def test_rejects_drop_outside_manifest_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest"
            manifest.mkdir()
            outside = root / "outside.bottle.json"
            outside.write_text("keep")
            plan = root / "plan.tsv"
            plan.write_text(f"DROP\t{outside}\tbad path\n")

            with self.assertRaisesRegex(ValueError, "not an active manifest"):
                MODULE.retire(plan, root / "candidates", manifest)
            self.assertTrue(outside.exists())


if __name__ == "__main__":
    unittest.main()
