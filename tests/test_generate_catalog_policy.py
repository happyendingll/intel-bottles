import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "generate_catalog.py"
SPEC = importlib.util.spec_from_file_location("generate_catalog", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class CatalogPolicyTests(unittest.TestCase):
    def test_versioned_formula_matches_excluded_family(self):
        families = {"mise", "node"}
        self.assertEqual("node", MODULE.matching_family("node", families))
        self.assertEqual("node", MODULE.matching_family("node@24", families))
        self.assertIsNone(MODULE.matching_family("node-build", families))


if __name__ == "__main__":
    unittest.main()
