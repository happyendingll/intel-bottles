# `catalog.txt` 生成与筛选规则

`catalog.txt` 是项目用来逐步增加新 Intel macOS bottle 的低优先级候选池。它从
Homebrew 的完整 Formula 集合自动生成，不是手工维护的清单，也不负责更新已经由本项目
维护的 bottle。

具体实现位于 [`scripts/generate_catalog.py`](../scripts/generate_catalog.py)。
[`generate prewarm catalog`](../.github/workflows/generate-catalog.yml) workflow 会在每次
`build bottles` 成功后，通过 `macos-15-intel` runner 运行该脚本。也可以手动执行该
workflow，并调整输出数量；默认保留 100 个候选 Formula。

## 整体流程

```text
Homebrew 全量 Formula
        │
        ▼
按过去 365 天 install-on-request 热度排序，其余按名称排序
        │
        ▼
兼容性检查和项目策略排除
        │
        ▼
在 macOS 15 Intel 上通过 Formula#bottled? 检查现有 bottle
        │
        ▼
递归检查依赖链中的阻断项
        │
        ▼
取前 N 个合格 Formula（默认 100）写入 catalog.txt
```

所有筛选阶段都会保持最开始的热度顺序。排在本轮数量上限之后的 Formula 只是暂缓，
不是永久排除；当前面的 Formula 编译成功或不再符合条件后，后面的候选会自然向前递补。

## 数据来源和排序

生成器会读取：

- Homebrew 完整 Formula 索引：`https://formulae.brew.sh/api/formula.json`；
- Homebrew 过去 365 天的 install-on-request 数据：
  `https://formulae.brew.sh/api/analytics/install-on-request/365d.json`；
- 在目标 runner 上准备好的自定义 `homebrew-core` fork；
- 本仓库中的策略文件和动态状态文件。

存在安装统计的 Formula 按 Homebrew 返回的热度顺序排列；其余 Formula 按名称排序后
追加。热度只决定优先级，不能绕过任何兼容性或项目策略检查。

## 第一层：直接排除

### 平台和生命周期不兼容

Formula API 的元数据符合以下任一条件时直接排除：

- 已被 Homebrew 禁用（`disabled`）；
- 已被废弃（`deprecated`）；
- 没有 stable 源码下载地址；
- 仅支持 Linux；
- 仅支持 arm64；
- 要求的最低 macOS 版本高于 macOS 15；
- 允许的最高 macOS 版本低于 macOS 15。

### `targets.txt`：已有 bottle 的强制更新队列

[`targets.txt`](../targets.txt) 中的 Formula 不进入可选预热。这些包已经由项目维护，
只是上游版本发生了变化，应该交给优先级更高的 `build bottles` 更新。

该文件由 `sync fork` 自动生成，不应把它当成 catalog 策略手动维护。

### `exclude.txt`：永久构建排除

[`exclude.txt`](../exclude.txt) 保存当前流水线无法或不应该构建的 Formula，例如超过
runner 时间上限的包、Intel 构建已损坏的包，以及被 Homebrew 移除的依赖。

不仅文件中直接列出的 Formula 会被排除，递归依赖它们的候选 Formula 也会被排除。

### `prewarm-failures.txt`：预热失败隔离区

[`prewarm-failures.txt`](../prewarm-failures.txt) 保存之前预热失败或超时的可选 Formula。
生成 catalog 时会排除这些 Formula 及其递归依赖者，避免每天重复消耗 runner 时间。

后续手动重试成功后，对应 Formula 可以从该隔离文件中自动移除。

### `catalog-policy.json`：优先使用上游二进制

[`catalog-policy.json`](../catalog-policy.json) 的 `exclude` 部分记录不推荐通过 Homebrew
源码编译的项目，例如官方明确建议使用自身 macOS 二进制发行版的工具。

这些 Formula 及其递归依赖者都会被排除。每条规则保留分类、原因和来源链接，方便以后
重新检查当时的判断是否仍然成立。

### 重型 Formula 家族

重型 Formula 来自 [`heavy.txt`](../heavy.txt) 和 `catalog-policy.json` 的
`heavy_formulae` 部分。家族匹配会覆盖带版本号的 Formula，例如 `node` 也会匹配
`node@24`，`llvm` 也会匹配 `llvm@22`。

重型 Formula 本身不会作为推测性的预热根包进入 catalog，但生成器仍会在目标 runner
上检查它们是否已有可用 bottle，因为这会决定依赖它们的普通 Formula 能否进入候选池：

- 重型依赖已有可用 Intel bottle：依赖它的普通 Formula 可以继续参加筛选；
- 重型依赖仍需源码编译：递归依赖它的所有候选 Formula 暂时排除。

这样可以防止一个看似很小、限制为一小时的 warm job，在内部意外开始编译 LLVM、GCC、
Rust、Qt WebEngine 或其他耗时数小时的基础依赖。

## 第二层：检查当前是否已有可用 bottle

通过静态筛选后，生成器会在真实的 `macos-15-intel` runner 上询问 Homebrew 每个
Formula 是否已有可用 bottle。判断使用 `Formula#bottled?`，同时设置：

```sh
HOMEBREW_NO_INSTALL_FROM_API=1
HOMEBREW_CORE_GIT_REMOTE=https://github.com/<owner>/homebrew-core
```

因此，下列两种来源的可用 bottle 都会被识别并排除：

- Homebrew 官方仍然提供的兼容 Intel macOS bottle；
- 本项目通过有效 manifest 写入自定义 `homebrew-core` fork 的 `sequoia` bottle。

只有在当前环境仍然需要源码编译的 Formula 才能继续参加筛选。如果 Formula API 中存在，
但目标 runner 准备好的 tap 无法加载它，则标记为 missing 并跳过。

## 第三层：递归依赖阻断

对于仍然缺少 bottle 的候选 Formula，生成器会使用 Formula API 元数据递归遍历运行依赖
和构建依赖。如果完整依赖链中包含以下任一内容，当前候选会被排除：

- `exclude.txt` 中的 Formula；
- `prewarm-failures.txt` 中的 Formula；
- `catalog-policy.json` 中优先使用上游二进制的 Formula；
- 当前仍然缺少 bottle 的重型 Formula。

该检查不能只看根 Formula。否则一个很小的根包也可能因为内部依赖已知失败项或重型组件，
耗尽整个 job 的时间。

## 输出数量和构建前的二次检查

生成器按照既定顺序写入前 `--limit` 个合格 Formula，默认数量为 100。超过数量上限的
Formula 仍然合格，只是留到后续生成轮次，不会写入任何永久排除文件。

真正开始构建前，[`scripts/plan_catalog.py`](../scripts/plan_catalog.py) 还会根据最新的
fork、`targets.txt`、`exclude.txt` 和 `prewarm-failures.txt` 再检查一次 `catalog.txt`。

这次二次检查用于处理 catalog 生成后到 warm build 启动前的状态变化，并避免已经被其他
任务成功编译的 Formula 再次进入构建矩阵。

## 如何理解生成统计

一次运行可能输出：

```text
catalog generation: scanned 8603, compatible 7832, recommended 100, rejected 796
```

各字段含义如下：

- `scanned`：本次 Homebrew 完整索引中的 Formula 数量；
- `compatible`：通过直接兼容性和项目策略检查的 Formula 数量；
- `recommended`：最终写入 `catalog.txt` 的数量，受 `--limit` 限制；
- `rejected`：已经得到明确拒绝原因的 Formula 数量，包括填满 catalog 过程中遇到的
  依赖阻断项。

`rejected` 并不等于 `scanned - recommended`。已经有 bottle 或无法加载的 Formula 会被
跳过；生成器填满指定数量后也不会继续检查所有排在后面的合格 Formula，因此后面的候选
没有被拒绝，只是还没有轮到。

上面的数字来自 2026-09-18 的一次运行，只是帮助理解字段的示例。随着 Homebrew、有效
manifest、`targets.txt` 和失败隔离文件变化，这些数字也会持续变化。
