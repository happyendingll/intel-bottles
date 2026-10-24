import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "patch_openjdk_boot_jdk.py"
SPEC = importlib.util.spec_from_file_location("patch_openjdk_boot_jdk", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def formula(arm_version: str = "27") -> str:
    return (
        "class Openjdk < Formula\n"
        '  url "https://github.com/openjdk/jdk27u/archive/refs/tags/jdk-27.0.1-ga.tar.gz"\n'
        '  resource "boot-jdk" do\n'
        "    on_macos do\n"
        f'      url "https://download.java.net/java/GA/jdk{arm_version}/'
        f'openjdk-{arm_version}_macos-aarch64_bin.tar.gz"\n'
        f'      sha256 "{"a" * 64}"\n'
        "    end\n"
        "    on_linux do\n"
        "      on_intel do\n"
        '        url "https://example.com/linux-x64.tar.gz"\n'
        "      end\n"
        "    end\n"
        "  end\n"
        "end\n"
    )


class PatchOpenJDKTests(unittest.TestCase):
    def test_adds_intel_boot_jdk_and_preserves_arm_and_linux(self):
        for version in ("27", "27.0.2"):
            with self.subTest(version=version):
                patched = MODULE.patch_text(formula(version))
                self.assertIn(f"openjdk-{version}_macos-aarch64", patched)
                self.assertIn(MODULE.INTEL_BOOT_URL, patched)
                self.assertIn(MODULE.INTEL_BOOT_SHA256, patched)
                self.assertIn("https://example.com/linux-x64.tar.gz", patched)
                self.assertEqual(MODULE.patch_text(patched), patched)

    def test_keeps_upstream_intel_fix(self):
        patched = MODULE.patch_text(formula())
        self.assertEqual(MODULE.patch_text(patched), patched)

    def test_fails_closed_when_upstream_resource_changes(self):
        changed = formula().replace("_macos-aarch64_bin.tar.gz", "_macos-universal_bin.tar.gz")
        with self.assertRaisesRegex(ValueError, "unexpected macOS boot-jdk"):
            MODULE.patch_text(changed)

    def test_fails_closed_when_openjdk_major_changes(self):
        changed = formula().replace("openjdk/jdk27u/", "openjdk/jdk28u/")
        with self.assertRaisesRegex(ValueError, "only valid for OpenJDK 27"):
            MODULE.patch_text(changed)


if __name__ == "__main__":
    unittest.main()
