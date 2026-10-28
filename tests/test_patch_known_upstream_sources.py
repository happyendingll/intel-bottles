import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "patch_known_upstream_sources.py"
SPEC = importlib.util.spec_from_file_location("patch_known_upstream_sources", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def formula(name: str) -> str:
    fix = MODULE.FIXES[name]
    return (
        f'class {fix["class"]} < Formula\n'
        f'  url "{fix["old_url"]}"\n'
        f'  sha256 "{fix["old_sha"]}"\n'
        '  license "MIT"\n'
        '  bottle do\n'
        '    sha256 cellar: :any, sequoia: "' + "a" * 64 + '"\n'
        '  end\n'
        '\n'
        'end\n'
    )


class KnownUpstreamSourcesTests(unittest.TestCase):
    def test_replaces_only_exact_known_source(self):
        for name, fix in MODULE.FIXES.items():
            with self.subTest(name=name):
                patched = MODULE.patch_text(name, formula(name))
                self.assertIn(f'  url "{fix["new_url"]}"', patched)
                self.assertIn(f'  sha256 "{fix["new_sha"]}"', patched)
                if name == "roadrunner":
                    self.assertNotIn("  bottle do\n", patched)
                else:
                    self.assertIn("  bottle do\n", patched)
                self.assertEqual(MODULE.patch_text(name, patched), patched)

    def test_upstream_version_url_or_checksum_change_disables_patch(self):
        for name, fix in MODULE.FIXES.items():
            with self.subTest(name=name):
                for changed in (
                    formula(name).replace(fix["old_url"], fix["old_url"].replace(".tar.gz", "-new.tar.gz")),
                    formula(name).replace(fix["old_sha"], "0" * 64),
                ):
                    self.assertEqual(MODULE.patch_text(name, changed), changed)

    def test_unexpected_formula_class_fails(self):
        with self.assertRaisesRegex(ValueError, "unexpected jfrog-cli Formula class"):
            MODULE.patch_text("jfrog-cli", formula("jfrog-cli").replace("JfrogCli", "Other"))


if __name__ == "__main__":
    unittest.main()
