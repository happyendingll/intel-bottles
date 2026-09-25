import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "patch_llvm_single_stage.py"
SPEC = importlib.util.spec_from_file_location("patch_llvm_single_stage", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def llvm_formula(version: str) -> str:
    return (
        f'  url "https://github.com/llvm/llvm-project/releases/download/llvmorg-{version}/'
        f'llvm-project-{version}.src.tar.xz"\n'
        "    pgo_build = build.stable? && build.bottle? && OS.mac? && !versioned_formula?\n"
        "    lto_build = pgo_build && OS.mac?\n"
    )


class PatchLLVMTests(unittest.TestCase):
    def test_patches_current_and_future_versions_without_version_pin(self):
        for version in ("23.1.1", "24.0.0"):
            with self.subTest(version=version):
                patched = MODULE.patch_text(llvm_formula(version))
                self.assertIn(f"llvmorg-{version}", patched)
                self.assertIn("    pgo_build = false", patched)
                self.assertIn("    lto_build = pgo_build && OS.mac?", patched)
                self.assertNotIn(MODULE.PGO_ASSIGNMENT, patched)

    def test_fails_closed_if_upstream_changes_pgo_control(self):
        changed = llvm_formula("24.0.0").replace(
            MODULE.PGO_ASSIGNMENT, "    pgo_build = build.bottle? && OS.mac?"
        )
        with self.assertRaisesRegex(ValueError, "PGO assignment"):
            MODULE.patch_text(changed)

    def test_fails_closed_if_upstream_changes_lto_control(self):
        changed = llvm_formula("24.0.0").replace(
            "    lto_build = pgo_build && OS.mac?", "    lto_build = true"
        )
        with self.assertRaisesRegex(ValueError, "LTO assignment"):
            MODULE.patch_text(changed)


if __name__ == "__main__":
    unittest.main()
