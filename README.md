# intel-bottles

Prebuilt Homebrew **bottles for Intel (x86_64) macOS**, built on GitHub Actions and consumed
through a fork of `homebrew-core`.

## Why

Homebrew moved Intel macOS to **Tier 3 in September 2026**: no CI, no new bottles. Support is
removed entirely in September 2027. The newest Intel bottles upstream are tagged `sonoma`
(macOS 14), so on macOS 15 every formula that has had a version bump since then compiles from
source — 72 of 368 installed formulae on the machine this was built for.

GitHub still offers **`macos-15-intel`**, its final x86_64 runner image, planned to remain
available **until August 2027**. It is free and unmetered on public repos. Homebrew dropped
Intel over maintainer burden, not hardware availability. So we build our own.

Bottles built there are tagged `sequoia` — an exact match for macOS 15 Intel. CI verifies this
tag before publishing so a mismatched runner cannot contaminate the fork.

## How it works

```
  sync fork       updates homebrew-core and writes stale active manifests to targets.txt
       ↓
  build bottles   publishes those updates in dependency-ordered waves
       ↓
  catalog         scans every Homebrew Formula and selects 100 eligible new candidates
       ↓
  prewarm         builds the new catalog entries in dependency-ordered waves
```

**Why roots, not one job per formula.** `brew install --build-bottle X` does *not* propagate
`--build-bottle` to X's dependencies — `install_dependency` in `formula_installer.rb` builds
its `FormulaInstaller` without it, so `brew bottle` would refuse them with *"Formula was not
installed with `--build-bottle`"*. So each job walks its root's chain in topological order
(`brew deps -n --include-build`) and explicitly builds only what still needs a bottle. One job
covers a whole subtree, and 72 formulae collapse to ~37 jobs.

**Why dependency waves.** Within a job the Cellar is shared, but across matrix jobs it is not.
Publishing widely shared roots in an earlier wave means later jobs pour them instead of
rebuilding them. The target planner auto-promotes anything at least five other unbottled
formulae depend on, so `qtbase` lands in an early wave without being listed anywhere.

**Optional prewarming.** `catalog.txt` is a generated, lower-priority pool for Formulae that
have never been bottled here. After every successful target build, catalog generation considers
the complete Homebrew Formula set, ranks entries with 365-day install-on-request analytics first,
then applies compatibility, current-bottle, cost, failure, and installation-policy filters before
writing 100 candidates. Heavy Formula families and projects that prefer their own optimized macOS
binary therefore never enter the catalog. Every successful prewarm writes an active manifest and
thereby joins the permanently maintained set.

A scheduled prewarm starts only after the post-build catalog refresh completes, selects up to
100 roots, and runs at most five jobs in parallel with a one-hour cap per job. Prewarmed assets
use numbered rolling Releases (`bottles-warm-1`, `bottles-warm-2`, and so on). Before a
Release approaches GitHub's 1,000-asset limit, the workflow advances to the next number. Old
Releases are retained because existing manifests keep their original `root_url`; new and
rebuilt Formulae point at the current rolling Release. All bottle blocks are merged into the
same `homebrew-core` fork.

**Consumption.** Bottle tarballs go to a rolling GitHub Release; `brew bottle --merge --write`
writes the matching `bottle do` blocks into a fork of `homebrew-core`, which the Mac points at
via `HOMEBREW_CORE_GIT_REMOTE`. Unqualified `brew install node` then just works, and no
`brew trust` is needed — brew still sees this as `homebrew/core`.

**Release cleanup.** Successful target and prewarm builds automatically delete the old bottle
asset after its replacement manifest has been pushed and only when no active manifest still
references it. `python3 scripts/prune_release_assets.py` handles historical leftovers: it first
performs a read-only audit; pass `--delete` only after reviewing the report. The script never
deletes a Release, refuses to use a stale local manifest commit, and requires explicit
confirmation (`--delete --yes` is available for intentional non-interactive use).

## Layout

| Path | Role |
|---|---|
| `targets.txt` | Generated queue of active manifests held for an upstream version refresh |
| `catalog.txt` | Lower-priority source of new Formulae to add to the maintained set |
| `catalog-policy.json` | Curated exclusions for upstream-binary-first and costly builds |
| `prewarm-failures.txt` | Failed/timed-out optional builds quarantined from future catalogs |
| `heavy.txt` | Forced into stage 1: expensive or risky |
| `scripts/generate_catalog.py` | Generates only compatible, missing, prewarm-suitable candidates |
| `scripts/plan_targets.py` | Picks what needs building, splits into stages |
| `scripts/plan_catalog.py` | Selects up to 100 missing optional roots, with a 60-minute job cap |
| `scripts/filter_unbottled.py` | Order-preserving "which of these lack a bottle here" |
| `scripts/build_root.sh` | Builds + bottles one root and its unbottled chain |
| `scripts/publish.sh` | Merges DSL into the fork, uploads release assets |
| `scripts/delete_replaced_assets.py` | Removes superseded assets after their new manifests are safely pushed |
| `scripts/prune_release_assets.py` | Audits unused Release bottles; deletes only with explicit confirmation |
| `scripts/apply_manifest.py` | Splits the manifest into still-valid vs stale |
| `scripts/sync_fork.sh` | Rebuilds the fork as upstream + our blocks |
| `manifest/` | Active `*.bottle.json` files — the source of truth for re-applying blocks; replaced versions remain recoverable from Git history |

## Runner assignment

`runners.json` decides which machine builds which formula. Everything uses the free
GitHub-hosted `macos-15-intel` unless listed under `assign`. The current assignment map is
empty; `qtwebengine` is excluded because it cannot finish inside GitHub's hard 6-hour ceiling.

```json
"assign": { "qtwebengine": "selfhosted" }
```

Moving a formula between runners is a one-line edit there; nothing else needs changing.

### Self-hosted runner

Register an Intel Mac running macOS 15 with the labels `self-hosted, macOS, X64` (Settings ->
Actions -> Runners). The `selfhosted` profile gives it a 48-hour timeout, since self-hosted
jobs are not bound by the 6-hour limit. A different macOS release will be rejected by the
`sequoia` bottle-tag check.

**Security note:** GitHub advises against self-hosted runners on public repositories,
because a fork's pull request could otherwise run arbitrary code on your machine. That
attack does not apply here — no workflow in this repo has a `pull_request` trigger; they
are all `workflow_dispatch`, `schedule` or `workflow_call`. Keep it that way, or move the
repo private (which costs runner minutes for the GitHub-hosted jobs).

## Setup

1. **Fork homebrew-core** to `<your-github-user>/homebrew-core` (keep the default branch `main`).
2. **Create this repo** as `<your-github-user>/intel-bottles`, **public** — standard runners are only
   free on public repos.
3. **Add a secret `FORK_TOKEN`**: a fine-grained PAT with `contents: write` on
   `<your-github-user>/homebrew-core`. Used to push rebuilt bottle blocks.
4. Run **sync fork** to generate the held refresh queue, then run **build bottles**. Scheduled
   runs do this in the same order; later builds only pick up active manifests whose upstream
   version has moved.

When changing the target macOS version, run **sync fork** once before **build bottles**. This
removes bottle blocks from the previous target before planning the new build.

## Client setup (the Intel Mac)

```sh
export HOMEBREW_NO_INSTALL_FROM_API=1
export HOMEBREW_CORE_GIT_REMOTE=https://github.com/<your-github-user>/homebrew-core
brew update
```

Trade-off: this swaps the fast JSON API for a full local `homebrew-core` git checkout, so
`brew update` and `brew search` get slower.

### Verify

```sh
brew info --json=v2 tmux | jq '.formulae[0].bottle.stable.files'   # expect a "sequoia" entry
brew reinstall tmux 2>&1 | grep -E 'Pouring|Building'             # expect "Pouring"
jq .poured_from_bottle /usr/local/Cellar/tmux/*/INSTALL_RECEIPT.json
```

## Known limits

- **`qtwebengine` does not fit in a GitHub job.** Measured, not predicted: it ran **5h50m**
  before hitting `timeout-minutes: 350`, and GitHub's hard job ceiling is 6 hours, so there
  was no headroom to give it. Disk was never the problem (~160 GB free throughout) — it is
  purely CPU time on 4 cores, and a single Chromium build cannot be split across jobs. It is
  pinned to stage 1 with `allow_failure: true` so it cannot take the run down. `qt`, `pyside`
  and `qtwebview` depend on it and stay unbottled with it. The only real options are a larger
  runner (more cores; billed even on public repos) or a self-hosted Intel runner.
- **One `root_url` per bottle block.** Merging our `sequoia` bottle into a formula that still has
  upstream's `sonoma` bottle rewrites the block's single `root_url` to ours. Harmless here —
  an exact tag match wins, so macOS 15 Intel always picks `sequoia` — but that block's older tags
  would not resolve on an older machine.
- **Three formulae are out of scope**, being outside `homebrew-core`: `packer` (hashicorp/tap),
  `ttab` (mklement0/ttab), and `valgrind` (a `HEAD` build, which cannot be bottled at all).
- **August 2027**: `macos-15-intel` is planned to be the last x86_64 image GitHub will offer.
  After that this pipeline needs a self-hosted Intel runner.
