#!/usr/bin/env python3
"""Apply narrow source fixes while the known broken upstream Formulae remain unchanged.

Each override requires the exact upstream URL and checksum observed on 2026-10-28.
Once Homebrew changes either field, sync leaves its new Formula alone.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


SOURCE = re.compile(r'^  url "(?P<url>[^"\n]+)"\n  sha256 "(?P<sha>[0-9a-f]{64})"\n', re.MULTILINE)
BOTTLE = re.compile(r'^  bottle do\n(?:    [^\n]*\n)+  end\n\n', re.MULTILINE)
FIXES = {
    "jfrog-cli": {
        "class": "JfrogCli",
        "old_url": "https://github.com/jfrog/jfrog-cli/archive/refs/tags/v2.128.0.tar.gz",
        "old_sha": "c592e0cb9b6a95a8e6f765a8b1b393fddac31770c23086a98713d5116dd8d849",
        "new_url": "https://github.com/jfrog/jfrog-cli/archive/refs/tags/v2.128.0.tar.gz",
        "new_sha": "57bdf75dc610179d8f60160afaf486b92162aeb85bb7fcc52e68aed8be1e0bf3",
    },
    "roadrunner": {
        "class": "Roadrunner",
        "old_url": "https://github.com/roadrunner-server/roadrunner/archive/refs/tags/v3.1.0.tar.gz",
        "old_sha": "4a5647cdfba543fe04347ba7658a65866508ba50463023750a36a1d900bedd36",
        "new_url": "https://github.com/roadrunner-server/roadrunner/archive/refs/tags/v3.0.1.tar.gz",
        "new_sha": "79cae54d8b3cc375d89f5dcdf3b89ab78d0c5ee281930936cb26de78a9171d33",
    },
}


def patch_text(name: str, text: str) -> str:
    fix = FIXES[name]
    if not text.startswith(f'class {fix["class"]} < Formula\n'):
        raise ValueError(f"unexpected {name} Formula class")
    match = SOURCE.search(text)
    if match is None:
        raise ValueError(f"could not find {name} stable source")
    if (match.group("url"), match.group("sha")) != (fix["old_url"], fix["old_sha"]):
        return text
    replacement = f'  url "{fix["new_url"]}"\n  sha256 "{fix["new_sha"]}"\n'
    patched = text[: match.start()] + replacement + text[match.end() :]
    if name == "roadrunner":
        # Upstream's bottle hashes belong to 3.1.0. They cannot be advertised
        # by the corrected 3.0.1 Formula; our Intel build will add its own.
        patched, count = BOTTLE.subn("", patched, count=1)
        if count != 1:
            raise ValueError("expected one roadrunner 3.1.0 bottle block")
    return patched


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=FIXES)
    parser.add_argument("formula", type=Path)
    args = parser.parse_args()
    original = args.formula.read_text()
    patched = patch_text(args.name, original)
    if patched == original:
        print(f"skipped {args.name}: upstream source no longer matches the known broken version")
    else:
        args.formula.write_text(patched)
        print(f"patched {args.name}: source matches the verified archive")


if __name__ == "__main__":
    main()
