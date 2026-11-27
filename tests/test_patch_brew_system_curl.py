import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.patch_brew_system_curl import SELECTOR, patch


class SystemCurlPatchTests(unittest.TestCase):
    def test_selection_with_and_without_opt_in(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "curl.sh"
            path.write_text("setup_curl() {\n" + SELECTOR + "}\n")
            patch(path)
            patched = path.read_text()
            patch(path)
            self.assertEqual(patched, path.read_text())
            for opt_in, expected in [
                ("1", ["curl", "7.41.0", "", "/usr/bin/curl", "", ""]),
                ("0", ["curl", "7.41.0", "/opt/curl", "/usr/bin/curl", "/custom/curl", "1"]),
            ]:
                with self.subTest(opt_in=opt_in):
                    result = subprocess.check_output(
                        [
                            "/bin/bash", "-c",
                            'select_tool() { printf "%s\\n" "$@"; }; source "$1"; setup_curl',
                            "test", str(path),
                        ],
                        env={
                            **os.environ,
                            "HOMEBREW_INTEL_BOTTLES_SYSTEM_CURL": opt_in,
                            "HOMEBREW_MINIMUM_CURL_VERSION": "7.41.0",
                            "HOMEBREW_BREWED_CURL_PATH": "/opt/curl",
                            "HOMEBREW_CURL_PATH": "/custom/curl",
                            "HOMEBREW_FORCE_BREWED_CURL": "1",
                        },
                        text=True,
                    )
                    self.assertEqual(expected, result.splitlines())

    def test_rejects_unknown_selector_without_editing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "curl.sh"
            path.write_text("unknown selector\n")
            with self.assertRaises(SystemExit):
                patch(path)
            self.assertEqual("unknown selector\n", path.read_text())
