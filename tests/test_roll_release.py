import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("roll_release", SCRIPTS / "roll_release.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class RollReleaseTests(unittest.TestCase):
    def test_warm_release_rolls_before_batch_crosses_safe_cap(self):
        releases = [
            {"tag_name": "bottles-warm-1"},
            {"tag_name": "bottles-warm-2"},
            {"tag_name": "bottles"},
        ]
        existing = {f"old-{number}" for number in range(850)}
        batch = {f"new-{number}" for number in range(51)}
        self.assertEqual(
            "bottles-warm-3",
            MODULE.choose_tag("bottles-warm-2", releases, existing, batch),
        )
        self.assertEqual(
            "bottles-warm-2",
            MODULE.choose_tag("bottles-warm-2", releases, existing, set(existing)),
        )

    def test_target_release_rolls_separately_from_warm_releases(self):
        releases = [
            {"tag_name": "bottles"},
            {"tag_name": "bottles-warm-2"},
        ]
        self.assertEqual(
            "bottles-2",
            MODULE.choose_tag("bottles", releases, {str(i) for i in range(900)}, {"new"}),
        )
        releases.append({"tag_name": "bottles-2"})
        self.assertEqual(
            "bottles-3",
            MODULE.choose_tag("bottles", releases, {str(i) for i in range(900)}, {"new"}),
        )

    def test_retarget_updates_only_the_batch_bottle_url(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tool--1.0.sequoia.bottle.json"
            payload = {
                "tool": {
                    "formula": {"pkg_version": "1.0"},
                    "bottle": {
                        "root_url": "https://github.com/owner/repo/releases/download/bottles-warm-2",
                        "tags": {"sequoia": {"sha256": "abc"}},
                    },
                }
            }
            path.write_text(json.dumps(payload))
            MODULE.retarget_json(
                [path],
                "https://github.com/owner/repo/releases/download/bottles-warm-2",
                "https://github.com/owner/repo/releases/download/bottles-warm-3",
            )
            updated = json.loads(path.read_text())["tool"]
            self.assertEqual(
                "https://github.com/owner/repo/releases/download/bottles-warm-3",
                updated["bottle"]["root_url"],
            )
            self.assertEqual("abc", updated["bottle"]["tags"]["sequoia"]["sha256"])


if __name__ == "__main__":
    unittest.main()
