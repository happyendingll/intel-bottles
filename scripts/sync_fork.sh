#!/usr/bin/env bash
#
# Rebuild the homebrew-core fork as: upstream plus bottle blocks that still match it.
#
# The fork is never hand-edited and never merged -- it is hard-reset onto upstream and the
# plan from apply_manifest.py is replayed on top, so merge conflicts cannot happen.
#
# When upstream advances a formula, its stale bottle is omitted. The following
# build-bottles run then sees the new formula as unbottled and publishes its replacement.

set -euo pipefail

: "${FORK_REPO:?FORK_REPO must be set}"

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CORE_REPO="$(brew --repo homebrew/core)"

echo "==> rebuilding $CORE_REPO from upstream"
cd "$CORE_REPO"
git remote get-url upstream >/dev/null 2>&1 \
  || git remote add upstream https://github.com/Homebrew/homebrew-core.git
git fetch --quiet upstream main
git fetch --quiet origin main

# Keep the fork's history linear. Resetting hard onto upstream and force-pushing rewrote
# history every night, and a consumer running `brew update` could then no longer
# fast-forward -- it left git conflict markers inside formula files, which made brew fail
# with a Ruby syntax error. Instead: start from the fork's current main, swap the working
# tree to upstream's content with read-tree, and commit that as an ordinary child. Same
# resulting content, but every push fast-forwards.
git checkout -q -B main origin/main
git read-tree --reset -u upstream/main

# Pin .github to whatever the fork already has, so our commits never touch workflow
# files. FORK_TOKEN deliberately has only contents:write, and GitHub refuses a push
# where a PAT without `workflow` scope creates or updates .github/workflows/*. Before
# this, upstream's own commits were fast-forwarded so the token never authored them;
# read-tree makes us the author of the whole tree, which tripped the restriction. The
# fork runs no workflows, so its .github content is irrelevant -- keeping it frozen is
# preferable to granting the token power to rewrite workflows.
git rm -r -q --cached .github >/dev/null 2>&1 || true
rm -rf .github
git checkout origin/main -- .github >/dev/null 2>&1 || true

echo "==> planning"
cd "$REPO_DIR"
PLAN="$(python3 scripts/apply_manifest.py)"

if [ -z "$PLAN" ]; then
  echo "nothing in the manifest to apply"
else
  # awk intentionally accepts a plan with no APPLY rows. grep under `set -o pipefail`
  # would turn that valid empty case into a sync failure.
  JSONS="$(printf '%s\n' "$PLAN" | awk -F '\t' '$1 == "APPLY" { print $2 }' | tr '\n' ' ')"
  if [ -n "${JSONS// /}" ]; then
    echo "==> re-applying bottle blocks"
    # shellcheck disable=SC2086 -- our own paths, no whitespace
    brew bottle --merge --write --no-commit $JSONS
  fi
fi

cd "$CORE_REPO"
git add -A
if git diff --cached --quiet; then
  echo "==> fork already matches upstream plus our blocks, nothing to push"
  exit 0
fi
git commit -q -m "Upstream sync + Intel bottle blocks ($(date -u +%Y-%m-%d))"

echo "==> pushing (fast-forward)"
if ! git push origin main; then
  echo "push was rejected -- the fork moved unexpectedly. Refusing to force." >&2
  echo "Inspect $CORE_REPO before retrying." >&2
  exit 1
fi
