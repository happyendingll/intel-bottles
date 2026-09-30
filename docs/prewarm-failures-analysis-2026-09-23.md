# 预热失败原因归档（2026-09-23）

本报告最初逐一核对 2026-09-23 当日 [`prewarm-failures.txt`](../prewarm-failures.txt) 中的 94 个 Formula，依据历史 `warm-bottles` job 日志归类。2026-09-28～29 的三次手动补编（[第一批](https://github.com/happyendingll/intel-bottles/actions/runs/36398508359)、[第二批](https://github.com/happyendingll/intel-bottles/actions/runs/36435197899)、[第三批](https://github.com/happyendingll/intel-bottles/actions/runs/36532738876)）覆盖原“约 60 分钟达到 job 上限”的 43 个包：其中 39 个构建 job 成功，已从本失败报告和当前隔离文件移除；余下 4 个依据新日志重新归类。当前保留 55 个未成功的历史记录；隔离文件还包含基准日期后新增的失败项，因此两者总数不同。构建 job 成功不等于 bottle 已发布。每个包只计入一个类别，类别按数量降序排列。包名链接直达对应 GitHub Actions job。

这是历史失败记录，不表示 Formula 现在仍缺官方 bottle，也不表示下次重试必然失败。尤其是接近 60 分钟被取消的 job，日志没有证明其源码无法编译；网络故障和 GitHub Artifact 上传故障也应与源码编译错误区分。日志不可用或输出不足时，明确标为无法确认。

| 类别 | 包数 |
|---|---:|
| 其他：独有原因或证据不足 | 15 |
| 依赖要求 arm64 | 7 |
| 缺构建工具、模块或头文件 | 6 |
| Formula 安装或链接冲突 | 5 |
| 网络解析失败或下载长期无响应 | 5 |
| 要求完整 Xcode.app | 4 |
| 下载源返回 HTTP 错误 | 3 |
| 下载内容 SHA256 不符 | 3 |
| 编译后上传 Artifact 失败 | 3 |
| 编译器不支持 `_Float16` | 2 |
| 接近 6 小时被取消，未见编译错误 | 2 |
| 约 60 分钟达到 job 上限 | 0 |
| **合计** | **55** |

## 1. 其他：独有原因或证据不足（15）

- [dotnet@8](https://github.com/happyendingll/intel-bottles/actions/runs/34775066010/job/103798616418)、[dotnet@9](https://github.com/happyendingll/intel-bottles/actions/runs/34837786911/job/103955666164)：源码构建退出 1；主日志有 VB/C# 编译服务器关闭警告，但不足以确认最终根因。
- [envoy](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856966552)：Bazel 构建失败；主日志没有足够信息进一步归因。
- [fpc](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093067476)：汇编器报告标签位于 `.cfi_startproc` 与 `.cfi_endproc` 之间的错误。
- [fricas](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332183512)：文档构建失败，`ht.db` 和 `.pht` 文件未生成。
- [haskell-language-server](https://github.com/happyendingll/intel-bottles/actions/runs/36532738876/job/109290158860)：手动补编时 `cabal v2-install` 报告 GHC 9.12.4 的非空包数据库缺少 `package.cache`；依赖安装失败后强制链接并重试一次，仍未恢复。
- [jackett](https://github.com/happyendingll/intel-bottles/actions/runs/34775066010/job/103798616407)：构建 `dotnet@9` 依赖时，VB/C# compiler server 关闭失败。
- [libtensorflow](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988872684)：Bazel 请求 runner 上不存在的 `macosx10.11` SDK。
- [logstash](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988873380)：Gradle bootstrap 报 `BUILD FAILED`；保留的日志没有展开根因。
- [mpv](https://github.com/happyendingll/intel-bottles/actions/runs/35382450939/job/105765889356)：无效的 `stolendata-mpv` Cask 定义阻断安装。
- [mycli](https://github.com/happyendingll/intel-bottles/actions/runs/34754920248/job/103738930739)：job 在约 1 小时 49 分后取消，历史日志不可用，不能断定为一小时构建超时。
- [openldap](https://github.com/happyendingll/intel-bottles/actions/runs/34775066010/job/103798616417)：Formula 的 `inreplace` 步骤失败。
- [powershell](https://github.com/happyendingll/intel-bottles/actions/runs/34775066010/job/103798616466)：出现 `dotnet` 符号链接冲突，随后 `dotnet restore` 失败；日志不足以证明两者的直接因果关系。
- [skip](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988879009)：job 记录为失败，但 GitHub 日志返回 `BlobNotFound`，无法确认原因。
- [wxpython](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093078626)：代码生成阶段缺少 `wxGLAttribsBase` 的 XML 文件。

## 2. 依赖要求 arm64（7）

这些包的依赖 graalvm、podman 或 mlx 等明确要求 Apple Silicon，当前 Intel runner 无法满足。

[astra](https://github.com/happyendingll/intel-bottles/actions/runs/35437021616/job/105881407050)、[astro](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856965524)、[cljfmt](https://github.com/happyendingll/intel-bottles/actions/runs/34930853524/job/104313226484)、[crip](https://github.com/happyendingll/intel-bottles/actions/runs/35067144987/job/104700194162)、[mlx-lm](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856969124)、[rapid-mlx](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093074702)、[signal-cli](https://github.com/happyendingll/intel-bottles/actions/runs/34775066010/job/103798616434)。

## 3. 缺构建工具、模块或头文件（6）

- `libusb.h` 缺失：[far2l-tty](https://github.com/happyendingll/intel-bottles/actions/runs/35437021616/job/105881407619)、[gammu](https://github.com/happyendingll/intel-bottles/actions/runs/35470174882/job/105969704123)、[libsidplayfp](https://github.com/happyendingll/intel-bottles/actions/runs/35437021616/job/105881408957)。
- 缺所需 libcurl 或 pkg-config：[freeswitch](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093067715)。
- 缺 Perl `URI::Escape`：[kdoctools](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332185922)。
- 缺 `git-lfs`：[odin](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856969799)。

## 4. Formula 安装或链接冲突（5）

- 冲突的已安装 Formula：[bazel](https://github.com/happyendingll/intel-bottles/actions/runs/35067144987/job/104700194130)、[bazel-diff](https://github.com/happyendingll/intel-bottles/actions/runs/34930853524/job/104313226030)。
- `dotnet` 可执行文件链接冲突：[garnet](https://github.com/happyendingll/intel-bottles/actions/runs/35067144987/job/104700196419)、[kiota](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332186034)。`kiota` 后续的 `dotnet publish` 也退出 1，不能仅凭日志确认两者因果关系。
- 与 runner 已安装的 yq 都提供 `yq` 命令：[python-yq](https://github.com/happyendingll/intel-bottles/actions/runs/35706692167/job/106677569263)。

## 5. 网络解析失败或下载长期无响应（5）

- `rubygems.org` DNS 解析失败：[jrsonnet](https://github.com/happyendingll/intel-bottles/actions/runs/35706692167/job/106677563821)。
- Git 获取超时：[librealsense](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093070426)。
- [mesheryctl](https://github.com/happyendingll/intel-bottles/actions/runs/36532738876/job/109290158859)：手动补编时 `brew fetch` 连续三次各超过 1,200 秒，最终报无法下载源码；日志未给出具体下载站点。
- `brew fetch` 连续两次超过 1,200 秒，随后触及 job 时限；日志未指出具体站点：[scotch](https://github.com/happyendingll/intel-bottles/actions/runs/34977393656/job/104408844449)。
- RubyGems 获取 gemspec 失败：[sequoia-sq](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332191582)。

## 6. 要求完整 Xcode.app（4）

日志要求完整 Xcode 26；只有 Command Line Tools 不足以构建。

[asccli](https://github.com/happyendingll/intel-bottles/actions/runs/35706692167/job/106677559746)、[cdo](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093064373)、[draw-things-cli](https://github.com/happyendingll/intel-bottles/actions/runs/35437021616/job/105881407564)、[vapor](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988881433)。

## 7. 下载源返回 HTTP 错误（3）

- 源码地址返回 404：[asdf](https://github.com/happyendingll/intel-bottles/actions/runs/35802884488/job/106997247465)、[ocm](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332189260)。
- 补丁地址返回 500：[coccinelle](https://github.com/happyendingll/intel-bottles/actions/runs/35533179699/job/106137682399)。

## 8. 下载内容 SHA256 不符（3）

[opencrabs](https://github.com/happyendingll/intel-bottles/actions/runs/35533179699/job/106137686638)、[ratify](https://github.com/happyendingll/intel-bottles/actions/runs/35533179699/job/106137687304)、[rosa-cli](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093075293)。这些包重试后仍提示下载内容与 Formula 声明的校验值不符。

## 9. 编译后上传 Artifact 失败（3）

[ecflow-ui](https://github.com/happyendingll/intel-bottles/actions/runs/35067144987/job/104700195383)、[kimi-code](https://github.com/happyendingll/intel-bottles/actions/runs/35356297416/job/105636713483)、[postgrest](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988876932)。构建后的 GitHub Artifact 上传分别出现请求超时或 `ENOTFOUND`；不应归咎于源码编译。

## 10. 编译器不支持 `_Float16`（2）

[fizz](https://github.com/happyendingll/intel-bottles/actions/runs/35382450939/job/105807657873)、[folly](https://github.com/happyendingll/intel-bottles/actions/runs/35382450939/job/105765887834)：均报告 `_Float16 is not supported on this target`。

## 11. 接近 6 小时被取消，未见编译错误（2）

- [graph-tool](https://github.com/happyendingll/intel-bottles/actions/runs/36532738876/job/109290158886)：手动补编已进入 `make install`，约 5 小时 49 分后 job 被取消；主日志未显示源码编译错误。
- [swift](https://github.com/happyendingll/intel-bottles/actions/runs/36532738876/job/109290161974)：手动补编已运行 `swift/utils/build-script`，约 5 小时 49 分后 job 被取消；主日志未显示源码编译错误。

两项都接近 GitHub 托管 runner 的 6 小时上限，但日志仅能确认“被取消”，不能据此断言源码无法编译。

## 12. 约 60 分钟达到 job 上限（0）

原有 43 项中，39 项的手动补编 job 成功，余下 4 项已依据新日志移至上述类别。保留本分类，供后续新出现的约 60 分钟超时 job 归档；单次超时本身不能证明源码编译失败。
