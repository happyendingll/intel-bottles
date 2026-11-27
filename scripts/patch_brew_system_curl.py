"""Give bottle builds an opt-in for Homebrew's system curl."""

import sys
from pathlib import Path


SELECTOR = """  select_tool curl "${HOMEBREW_MINIMUM_CURL_VERSION}" "${HOMEBREW_BREWED_CURL_PATH}" \\
    /usr/bin/curl "${HOMEBREW_CURL_PATH}" "${HOMEBREW_FORCE_BREWED_CURL}"
"""

PATCHED_SELECTOR = """  if [[ "${INTEL_BOTTLES_SYSTEM_CURL:-}" == 1 ]]
  then
    HOMEBREW_BREWED_CURL_PATH=/usr/bin/curl
    select_tool curl "${HOMEBREW_MINIMUM_CURL_VERSION}" "" /usr/bin/curl "" ""
  else
""" + "".join(f"  {line}" for line in SELECTOR.splitlines(keepends=True)) + "  fi\n"


def patch(path: Path) -> None:
    source = path.read_text()
    if source.count(PATCHED_SELECTOR) == 1:
        return
    if source.count(SELECTOR) != 1:
        raise SystemExit(f"{path}: Homebrew's curl selector changed; review before building")
    path.write_text(source.replace(SELECTOR, PATCHED_SELECTOR, 1))


if __name__ == "__main__":
    patch(Path(sys.argv[1]))
