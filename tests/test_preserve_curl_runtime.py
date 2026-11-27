import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "preserve_curl_runtime.sh"
BUILD_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_root.sh"


def executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class PreserveCurlRuntimeTests(unittest.TestCase):
    def run_guard(self, linked_formula: str, requested_formula: str):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        bin_dir = root / "bin"
        curl_prefix = root / "curl"
        formula_prefix = root / requested_formula
        temp_dir = root / "tmp"
        bin_dir.mkdir()
        temp_dir.mkdir()
        (curl_prefix / "bin").mkdir(parents=True)
        (formula_prefix / "lib").mkdir(parents=True)
        executable(curl_prefix / "bin" / "curl", "#!/bin/sh\nexit 0\n")
        (formula_prefix / "lib" / "libzstd.1.dylib").write_text("preserved")
        (formula_prefix / "lib" / "libzstd.dylib").symlink_to("libzstd.1.dylib")

        executable(
            bin_dir / "brew",
            f"""#!/bin/sh
if [ "$2" = curl ]; then
  printf '%s\\n' '{curl_prefix}'
else
  printf '%s\\n' '{formula_prefix}'
fi
""",
        )
        executable(
            bin_dir / "otool",
            f"""#!/bin/sh
printf '%s:\\n' "$2"
printf '\\t%s/lib/libzstd.1.dylib (compatibility version 1.0.0)\\n' '{root / linked_formula}'
""",
        )
        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env['PATH']}"
        env["TMPDIR"] = str(temp_dir)
        result = subprocess.run(
            ["bash", str(SCRIPT), requested_formula],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        return temporary, result.stdout.strip()

    def test_copies_all_dylib_names_when_curl_uses_formula(self):
        temporary, output = self.run_guard("zstd", "zstd")
        with temporary:
            fallback = Path(output)
            self.assertEqual("preserved", (fallback / "libzstd.1.dylib").read_text())
            self.assertEqual("preserved", (fallback / "libzstd.dylib").read_text())

    def test_prints_nothing_for_unrelated_formula(self):
        temporary, output = self.run_guard("zstd", "glib")
        with temporary:
            self.assertEqual("", output)

    def test_build_guards_uninstall_and_restores_after_install(self):
        script = BUILD_SCRIPT.read_text()
        preserve = script.index('preserve_curl_runtime.sh" "$formula"')
        uninstall = script.index('brew uninstall --ignore-dependencies --force "$formula"')
        install = script.index('brew install --build-bottle --display-times "$formula"')
        restore = script.index("restore_curl_runtime_fallback", install)
        self.assertLess(preserve, uninstall)
        self.assertLess(uninstall, install)
        self.assertLess(install, restore)


if __name__ == "__main__":
    unittest.main()
