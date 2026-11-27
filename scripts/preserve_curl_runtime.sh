#!/usr/bin/env bash
# Copy a formula's dylibs when Homebrew's brewed curl links against that formula.
# Prints the fallback directory, or nothing when no guard is needed.

set -euo pipefail

formula="${1:?usage: preserve_curl_runtime.sh <formula>}"

curl_prefix="$(brew --prefix curl 2>/dev/null || true)"
formula_prefix="$(brew --prefix "$formula" 2>/dev/null || true)"
curl_bin="$curl_prefix/bin/curl"

if [ ! -x "$curl_bin" ] || [ ! -d "$formula_prefix/lib" ]; then
  exit 0
fi

linked=0
while IFS= read -r dylib; do
  case "$dylib" in
    "$formula_prefix"/*)
      linked=1
      break
      ;;
  esac
done <<EOF
$(otool -L "$curl_bin" | awk 'NR > 1 { print $1 }')
EOF

if [ "$linked" != 1 ]; then
  exit 0
fi

runtime_dir="$(mktemp -d "${TMPDIR:-/tmp}/intel-bottles-curl-runtime.XXXXXX")"
copied=0
while IFS= read -r dylib; do
  cp -L "$dylib" "$runtime_dir/$(basename "$dylib")"
  copied=1
done <<EOF
$(find "$formula_prefix/lib" \( -type f -o -type l \) -name '*.dylib' -print)
EOF

if [ "$copied" != 1 ]; then
  echo "brew curl links to $formula but no dylibs could be preserved" >&2
  exit 1
fi

printf '%s\n' "$runtime_dir"
