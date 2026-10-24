#!/usr/bin/env python3
"""Use an Intel macOS Boot JDK when building the unversioned OpenJDK Formula.

The upstream Formula currently selects an aarch64 JDK for every macOS host.
Keep its ARM resource unchanged, and use the last available macOS x64 JDK 26
as the Boot JDK for building JDK 27 on our Intel runner.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


INTEL_BOOT_URL = (
    "https://download.java.net/java/GA/jdk26.0.2.1/"
    "3b8e6c7ec6274148a7aa15e7e7dfb53c/1/GPL/"
    "openjdk-26.0.2.1_macos-x64_bin.tar.gz"
)
INTEL_BOOT_SHA256 = "5ec3817530ffa1c38f15a55609a2767335bbd0c59ea8ce41aad68d3cd620c0ae"

MACOS_RESOURCE = re.compile(
    r'    on_macos do\n'
    r'      url "(?P<url>https://download\.java\.net/java/GA/[^"\n]+_macos-aarch64_bin\.tar\.gz)"\n'
    r'      sha256 "(?P<sha256>[0-9a-f]{64})"\n'
    r'    end\n'
)


def patch_text(text: str) -> str:
    if not re.search(r'^  url "https://github\.com/openjdk/jdk27u/', text, re.MULTILINE):
        raise ValueError("Intel JDK 26 Boot JDK override is only valid for OpenJDK 27")
    marker = '  resource "boot-jdk" do\n'
    if text.count(marker) != 1:
        raise ValueError("expected exactly one OpenJDK boot-jdk resource")
    before, resource = text.split(marker, 1)
    if "    on_linux do\n" not in resource:
        raise ValueError("expected Linux branch after macOS boot-jdk resource")
    macos, linux_and_after = resource.split("    on_linux do\n", 1)

    # Upstream may eventually restore its own Intel resource. Keep that fix.
    if "      on_intel do\n" in macos:
        if "_macos-x64_bin.tar.gz" not in macos:
            raise ValueError("Intel boot-jdk branch has no macOS x64 archive")
        return text

    match = MACOS_RESOURCE.fullmatch(macos)
    if match is None:
        raise ValueError("unexpected macOS boot-jdk resource; review upstream Formula")
    url, sha256 = match.group("url", "sha256")
    patched_macos = (
        "    on_macos do\n"
        "      on_arm do\n"
        f'        url "{url}"\n'
        f'        sha256 "{sha256}"\n'
        "      end\n"
        "      on_intel do\n"
        f'        url "{INTEL_BOOT_URL}"\n'
        f'        sha256 "{INTEL_BOOT_SHA256}"\n'
        "      end\n"
        "    end\n"
    )
    return before + marker + patched_macos + "    on_linux do\n" + linux_and_after


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("formula", type=Path)
    args = parser.parse_args()
    original = args.formula.read_text()
    patched = patch_text(original)
    if patched != original:
        args.formula.write_text(patched)
        print(f"patched {args.formula}: macOS Intel uses JDK 26.0.2.1 x64 as Boot JDK")
    else:
        print(f"already has a macOS Intel Boot JDK: {args.formula}")


if __name__ == "__main__":
    main()
