#!/usr/bin/env bash
# Put Homebrew/brew and the core tap into deterministic, current states on a CI runner.

set -euo pipefail

if [ "${CI:-}" != "true" ] && [ "${ALLOW_LOCAL_PREPARE:-}" != "1" ]; then
  echo "refusing to replace local Homebrew checkouts outside disposable CI" >&2
  exit 1
fi
: "${HOMEBREW_CORE_GIT_REMOTE:?HOMEBREW_CORE_GIT_REMOTE must be set}"

# Runner images can lag behind homebrew-core. For example, core started using
# Formula#python3 before the macos-15 image's bundled brew contained that helper.
# Update brew itself without `brew update`, whose stash/pop of local tap changes can
# leave formulae containing unresolved conflict markers.
BREW_REPO="$(brew --repository)"
git -C "$BREW_REPO" fetch --quiet --force --tags origin
LATEST_BREW_TAG="$(git -C "$BREW_REPO" tag --list --sort=-version:refname | sed -n '1p')"
if [ -z "$LATEST_BREW_TAG" ]; then
  echo "could not determine the latest Homebrew release tag" >&2
  exit 1
fi
git -C "$BREW_REPO" checkout -q -f -B stable "refs/tags/$LATEST_BREW_TAG"

brew tap homebrew/core 2>/dev/null || true
CORE_REPO="$(brew --repo homebrew/core)"
git -C "$CORE_REPO" remote set-url origin "$HOMEBREW_CORE_GIT_REMOTE"
git -C "$CORE_REPO" fetch --quiet origin main
git -C "$CORE_REPO" checkout -q -f -B main origin/main

echo "Homebrew: $(brew --version | sed -n '1p') ($(git -C "$BREW_REPO" rev-parse --short HEAD))"
echo "core tap: $CORE_REPO ($(git -C "$CORE_REPO" rev-parse --short HEAD))"
