# intel-bottles

[中文说明](#中文说明) · [English documentation](#english-documentation)

## 中文说明

### 项目概述

`intel-bottles` 为 **Intel（x86_64）macOS 15 Sequoia** 持续补充 Homebrew bottle。
项目不替代 Homebrew，也不维护一套独立 Formula：它同步官方 `homebrew-core`，只把缺失的
Intel bottle 构建出来，再把对应的 `bottle do` 信息写入个人 `homebrew-core` fork。

客户端仍然使用熟悉的 `brew install` 和 `brew upgrade`；区别只是 Formula 定义来自这个
fork，因此 Homebrew 能直接下载 `sequoia` bottle，而不必在 Intel Mac 上等待源码编译。

> 核心目标不是维护一份固定的包清单，而是维护一个会持续增长、能够自动跟随上游版本更新
> 的 Intel bottle 集合。

### 闭环设计

```mermaid
flowchart TB
  subgraph refresh["维护闭环：让已有 bottle 持续跟上官方版本"]
    U["官方 homebrew-core"] --> S["sync fork<br/>同步上游并重放有效 manifest"]
    M[("manifest/*.bottle.json<br/>当前全部维护对象")] --> S
    S --> F[("个人 homebrew-core fork<br/>官方 Formula + 有效 bottle block")]
    S --> T["targets.txt<br/>版本已变化、需要重建的队列"]
    T --> B["build bottles<br/>按依赖深度分 wave"]
    B --> P["构建、装瓶并发布"]
    P --> M
    P --> F
    P --> R[("GitHub Releases<br/>实际 bottle 资产")]
    P --> D["安全删除已被替换且<br/>不再被 manifest 引用的旧资产"]
  end

  subgraph growth["增长闭环：逐步补齐尚未维护的新 Formula"]
    A["Homebrew 全量 Formula<br/>+ 365 天安装热度"] --> G["generate catalog<br/>兼容性、策略、bottle、依赖链筛选"]
    F --> G
    X["exclude / heavy / catalog-policy<br/>prewarm-failures"] --> G
    G --> C["catalog.txt<br/>本轮优先的 100 个新候选"]
    C --> W["warm bottles<br/>再次去重并按 wave 预热"]
    W -->|成功| WP["发布新 bottle"]
    WP --> M
    WP --> F
    WP --> R
    W -->|失败或超时| Q["prewarm-failures.txt<br/>隔离，避免下一轮重复消耗"]
    Q --> G
  end

  subgraph observe["观察与人工决策"]
    H["每日检查重型基础依赖版本"] -->|落后或缺失| I["GitHub Issue / 邮件提醒"]
    I -. 手动决定普通构建或专用构建 .-> B
  end

  M -. 上游下一次升级后重新进入维护闭环 .-> S
  B -->|成功后自动触发| G
```

这张图表达了三个关键意图：

1. **已有 bottle 会持续更新。** `manifest/` 是维护集合的事实来源。上游版本变化后，
   `sync fork` 不再套用旧 bottle，而是把它放进 `targets.txt`；构建成功后，新 manifest
   替换旧版本，重新闭合维护循环。
2. **维护集合会持续增长。** `catalog.txt` 只负责发现尚未维护的新 Formula。任何 warm
   build 成功的 Formula 都会写入 `manifest/`，从下一轮开始自动进入上面的版本维护闭环。
   因此维护数量不是固定值，会随着预热成功不断增加。
3. **失败不会无限重复。** 可选预热失败或超过一小时的 Formula 会进入
   `prewarm-failures.txt`，下一次生成 catalog 时连同依赖它的候选一起过滤。重型基础依赖
   则单独监控和提醒，由维护者决定是否使用专用工作流构建。

更完整的 catalog 筛选细节见
[`catalog.txt` 生成与筛选规则](docs/catalog-generation.md)。

### 自动运行顺序

| 顺序 | Workflow | 作用 | 下一步 |
|---:|---|---|---|
| 1 | [`sync-fork.yml`](.github/workflows/sync-fork.yml) | 同步官方 core、重放版本仍匹配的 manifest，并生成 held 更新队列 | 等待定时 `build bottles` |
| 2 | [`build-bottles.yml`](.github/workflows/build-bottles.yml) | 更新 `targets.txt` 中已经维护但版本落后的 bottle | 成功后触发 `generate catalog` |
| 3 | [`generate-catalog.yml`](.github/workflows/generate-catalog.yml) | 从全量 Formula 中筛出本轮最值得新增的 100 个候选 | 成功后触发 `warm bottles` |
| 4 | [`warm-bottles.yml`](.github/workflows/warm-bottles.yml) | 分 wave 构建新候选；成功项加入长期维护集合，失败项进入隔离文件 | 回到下一轮同步与筛选 |

此外还有两个辅助入口：

- [`check-heavy-updates.yml`](.github/workflows/check-heavy-updates.yml)：每天比较重型基础依赖的
  官方版本和有效 manifest；有缺口时创建并指派 Issue，通过 GitHub 通知邮件提醒。
- [`build-llvm-single-stage.yml`](.github/workflows/build-llvm-single-stage.yml)：LLVM 专用手动入口，
  跳过耗时很长的 PGO 多阶段构建，在 Intel runner 上生成可用的单阶段 bottle。

### 为什么使用依赖 wave

GitHub 的每个 matrix job 都是隔离环境。如果所有 Formula 同时启动，多个 job 可能分别从
源码重复构建 `qtbase`、LLVM 或其他共享依赖。规划器先计算缺失依赖之间的深度：

```text
wave 0：没有其他待构建依赖的基础包
   ↓ 发布 bottle
wave 1：可以直接使用 wave 0 bottle 的包
   ↓ 发布 bottle
wave 2～4：继续复用前面 wave 的成果
```

每个 wave 发布完成后才进入下一个 wave，后续 job 会直接 pour 已发布依赖。这是降低总编译
时间、避免相同重型依赖被多次源码编译的核心设计。

### 四类核心状态文件

| 文件 | 谁维护 | 表示什么 | 是否直接构建 |
|---|---|---|---|
| [`manifest/`](manifest/) | 发布流程自动写入 | 所有已经成功构建、今后必须持续更新的 bottle；项目事实来源 | 版本变化后进入 `targets.txt` |
| [`targets.txt`](targets.txt) | `sync fork` 自动覆盖 | 当前维护集合中版本已经落后的 Formula | 是，最高优先级 |
| [`catalog.txt`](catalog.txt) | `generate catalog` 自动覆盖 | 尚未维护、通过筛选的本轮新增候选 | 是，低于 targets |
| [`prewarm-failures.txt`](prewarm-failures.txt) | warm 发布流程更新 | 曾经失败或超时的可选预热 Formula | 否，成功重试后可移除 |

必须注意：`targets.txt` 不是用户想安装的软件列表，`catalog.txt` 也不是全部维护对象。
真正代表项目长期维护范围的是 `manifest/` 根目录下的全部有效 JSON。

### 策略与执行文件

| 文件 | 职责 |
|---|---|
| [`exclude.txt`](exclude.txt) | 永久排除当前环境无法完成或不应该构建的 Formula，并阻断其递归依赖者 |
| [`heavy.txt`](heavy.txt) | 标记需要独立处理的重型基础依赖家族 |
| [`catalog-policy.json`](catalog-policy.json) | 记录优先使用官方二进制、成本过高等可审计策略及原因 |
| [`runners.json`](runners.json) | 为特殊 Formula 分配 runner 类型和超时时间 |
| [`scripts/apply_manifest.py`](scripts/apply_manifest.py) | 把有效 manifest 与版本已变化的 held 项分开 |
| [`scripts/generate_catalog.py`](scripts/generate_catalog.py) | 从全量 Formula 生成经过策略和依赖链过滤的新增候选 |
| [`scripts/plan_targets.py`](scripts/plan_targets.py) | 规划强制更新队列的依赖 wave |
| [`scripts/plan_catalog.py`](scripts/plan_catalog.py) | 在构建前复查 catalog、去重并规划预热 wave |
| [`scripts/build_root.sh`](scripts/build_root.sh) | 按拓扑顺序构建一个根 Formula 及其仍缺 bottle 的依赖链 |
| [`scripts/publish.sh`](scripts/publish.sh) | 上传 bottle、写入 manifest，并把 bottle block 合并进 core fork |
| [`scripts/delete_replaced_assets.py`](scripts/delete_replaced_assets.py) | 新版本安全落地后删除不再被有效 manifest 引用的旧资产 |

### 发布结果为什么分成三部分

一次构建只有同时完成以下三项才真正闭环：

- **Release 资产**：保存 `.bottle.tar.gz`，是客户端下载的实际文件；
- **manifest**：记录版本、SHA256、Release 地址和 Formula 路径，是项目恢复与持续更新的依据；
- **homebrew-core fork**：保存带 `sequoia` bottle block 的 Formula，让客户端 Homebrew 知道
  应该下载哪个资产。

manifest 中的 `root_url` 会指向 bottle 实际所在的滚动 Release。旧 Release 不能仅因为已经
启用新编号就整体删除，因为仍有有效 manifest 可能引用它；只有被新版本替换且已无任何
有效 manifest 引用的单个资产才会自动清理。

### Intel Mac 使用方式

不要把自定义 Core 环境变量全局 `export`。在 `~/.zshrc`（使用 Bash 时为 `~/.bashrc`）中
定义一个只影响单次命令的中转函数：

```sh
brew-intel() {
  HOMEBREW_NO_INSTALL_FROM_API=1 \
  HOMEBREW_CORE_GIT_REMOTE=https://github.com/happyendingll/homebrew-core \
    command brew "$@"
}
```

重新打开终端或执行 `source ~/.zshrc` 后，两个入口各自负责一类包：

```sh
brew upgrade --cask          # 官方 Homebrew API、官方 Cask 定义和原厂软件下载地址
brew-intel upgrade --formula # 自定义 homebrew-core fork 和本项目的 Intel bottle
```

`HOMEBREW_CORE_GIT_REMOTE` 只改变 `homebrew/core` 的 Git remote，不会把 Cask 指向本项目；
但 [Homebrew 官方文档](https://docs.brew.sh/Installation#default-tap-cloning)明确说明，
`HOMEBREW_NO_INSTALL_FROM_API=1` 会让 Formula 和 Cask 改用本地 `homebrew/core`、
`homebrew/cask` checkout，而不是默认 API。如果把它全局导出，普通 Cask 命令也会离开默认的
快速 JSON API 路径，可能增加 Git checkout 占用，并让 `brew update` 变慢。

通过 `brew-intel` 函数按命令临时设置变量，可以把这种本地 Git 模式限制在需要自定义 Core
的 Formula 操作中；函数返回后环境不会残留，普通 `brew` 的 Cask 安装和更新继续使用
Homebrew 默认 API，安装文件仍从官方 Cask 定义指定的软件厂商地址下载。

可以再定义一个完整更新函数，把 Cask 和 Formula 按各自入口顺序更新：

```sh
brew-update-all() {
  brew update &&
    brew upgrade --cask &&
    brew cleanup &&
    brew-intel update &&
    brew-intel upgrade --formula &&
    brew-intel cleanup
}
```

以后执行一次即可：

```sh
brew-update-all
```

这里不需要 `brew upgrade --cask --all`：
[Homebrew `upgrade` 文档](https://docs.brew.sh/Manpage#upgrade-options-installed_formula-installed_cask-)
规定，`--cask` 后不指定名称时本身就表示升级所有 outdated Cask；
`brew-intel upgrade --formula` 同理会升级所有过期且未固定的 Formula。

---

## English documentation

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

A detailed Chinese reference is available in
[`catalog.txt` 生成与筛选规则](docs/catalog-generation.md), including the exact filter order,
dynamic quarantine files, heavyweight dependency handling, and generation statistics.

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
| `docs/catalog-generation.md` | `catalog.txt` 全量筛选、依赖阻断与排序规则（中文） |

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

Keep the default `brew` path for official casks and scope the custom Core settings to a shell
function (for example in `~/.zshrc`):

```sh
brew-intel() {
  HOMEBREW_NO_INSTALL_FROM_API=1 \
  HOMEBREW_CORE_GIT_REMOTE=https://github.com/happyendingll/homebrew-core \
    command brew "$@"
}

brew-update-all() {
  brew update &&
    brew upgrade --cask &&
    brew cleanup &&
    brew-intel update &&
    brew-intel upgrade --formula &&
    brew-intel cleanup
}
```

Run `brew-update-all` for a combined update. Normal `brew` commands retain Homebrew's fast API
and official cask definitions; `brew-intel` temporarily enables the local Core checkout and
custom `homebrew-core` fork. This avoids globally forcing cask metadata onto the larger, slower
Git-checkout path. Cask application downloads still use the vendor URLs in official cask
definitions. See Homebrew's documentation for
[`HOMEBREW_NO_INSTALL_FROM_API`](https://docs.brew.sh/Installation#default-tap-cloning) and
[`brew upgrade`](https://docs.brew.sh/Manpage#upgrade-options-installed_formula-installed_cask-).

### Verify

```sh
brew-intel info --json=v2 tmux | jq '.formulae[0].bottle.stable.files' # expect "sequoia"
brew-intel reinstall tmux 2>&1 | grep -E 'Pouring|Building'           # expect "Pouring"
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
