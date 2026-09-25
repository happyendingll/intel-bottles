# 预热失败原因归档（2026-09-23）

本报告逐一核对当日 [`prewarm-failures.txt`](../prewarm-failures.txt) 中的 94 个 Formula，依据历史 `warm-bottles` job 日志归类。每个包只计入一个类别，类别按数量降序排列。包名链接直达对应 GitHub Actions job。

这是历史失败记录，不表示 Formula 现在仍缺官方 bottle，也不表示下次重试必然失败。尤其是接近 60 分钟被取消的 job，日志没有证明其源码无法编译；网络故障和 GitHub Artifact 上传故障也应与源码编译错误区分。日志不可用或输出不足时，明确标为无法确认。

| 类别 | 包数 |
|---|---:|
| 约 60 分钟达到 job 上限 | 43 |
| 其他：独有原因或证据不足 | 14 |
| 依赖要求 arm64 | 7 |
| 缺构建工具、模块或头文件 | 6 |
| Formula 安装或链接冲突 | 5 |
| 要求完整 Xcode.app | 4 |
| 网络解析失败或下载长期无响应 | 4 |
| 下载源返回 HTTP 错误 | 3 |
| 下载内容 SHA256 不符 | 3 |
| 编译后上传 Artifact 失败 | 3 |
| 编译器不支持 `_Float16` | 2 |
| **合计** | **94** |

## 1. 约 60 分钟达到 job 上限（43）

这些 job 在约一小时处取消；不能仅凭这个状态断言其源码存在编译错误。

[aider](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856965518)、[aoe](https://github.com/happyendingll/intel-bottles/actions/runs/35356297416/job/105729933871)、[aws-sdk-cpp](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856965477)、[blast](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988866584)、[cake](https://github.com/happyendingll/intel-bottles/actions/runs/35470174882/job/105991834518)、[dart-sdk](https://github.com/happyendingll/intel-bottles/actions/runs/35050695162/job/104650407575)、[datafusion](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332182110)、[dotnet](https://github.com/happyendingll/intel-bottles/actions/runs/35470174882/job/105969703357)、[dstack](https://github.com/happyendingll/intel-bottles/actions/runs/34930853524/job/104313229314)、[emscripten](https://github.com/happyendingll/intel-bottles/actions/runs/35356297416/job/105636710701)、[flang](https://github.com/happyendingll/intel-bottles/actions/runs/35382450939/job/105765887743)、[foundry](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988869964)、[graph-tool](https://github.com/happyendingll/intel-bottles/actions/runs/35382450939/job/105765887980)、[graphviz2drawio](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332184682)。

[haskell-language-server](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093069054)、[hermes-agent](https://github.com/happyendingll/intel-bottles/actions/runs/35356297416/job/105636712688)、[influxdb](https://github.com/happyendingll/intel-bottles/actions/runs/34837786911/job/103955666267)、[ironclaw](https://github.com/happyendingll/intel-bottles/actions/runs/35356297416/job/105636712930)、[joplin-cli](https://github.com/happyendingll/intel-bottles/actions/runs/35356297416/job/105729933998)、[letta-code](https://github.com/happyendingll/intel-bottles/actions/runs/35356297416/job/105729933981)、[librefang](https://github.com/happyendingll/intel-bottles/actions/runs/35533179699/job/106137685385)、[mercury](https://github.com/happyendingll/intel-bottles/actions/runs/35533179699/job/106137685821)、[mesheryctl](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988874094)、[mold](https://github.com/happyendingll/intel-bottles/actions/runs/34837786911/job/103955667592)、[mongodb-atlas-cli](https://github.com/happyendingll/intel-bottles/actions/runs/35356297416/job/105729934032)、[netlify-cli](https://github.com/happyendingll/intel-bottles/actions/runs/35356297416/job/105729933904)、[nift](https://github.com/happyendingll/intel-bottles/actions/runs/35706692167/job/106677566926)、[oterm](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988875434)。

[pake](https://github.com/happyendingll/intel-bottles/actions/runs/35356297416/job/105729934043)、[pdfly](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856970225)、[ponyc](https://github.com/happyendingll/intel-bottles/actions/runs/34930853524/job/104313234260)、[prowler](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856970529)、[pup](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856970579)、[pytorch](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856970780)、[root](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856971101)、[sing-box](https://github.com/happyendingll/intel-bottles/actions/runs/35382450939/job/105765890698)、[solana](https://github.com/happyendingll/intel-bottles/actions/runs/35382450939/job/105765891099)、[stellar-core](https://github.com/happyendingll/intel-bottles/actions/runs/35437021616/job/105881410912)、[sui](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856971862)、[swift](https://github.com/happyendingll/intel-bottles/actions/runs/35802884488/job/106997255082)、[technitium-dns](https://github.com/happyendingll/intel-bottles/actions/runs/35470174882/job/105991834530)、[v8](https://github.com/happyendingll/intel-bottles/actions/runs/35382450939/job/105765892880)、[vtk](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856972650)。

## 2. 其他：独有原因或证据不足（14）

- [dotnet@8](https://github.com/happyendingll/intel-bottles/actions/runs/34775066010/job/103798616418)、[dotnet@9](https://github.com/happyendingll/intel-bottles/actions/runs/34837786911/job/103955666164)：源码构建退出 1；主日志有 VB/C# 编译服务器关闭警告，但不足以确认最终根因。
- [envoy](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856966552)：Bazel 构建失败；主日志没有足够信息进一步归因。
- [fpc](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093067476)：汇编器报告标签位于 `.cfi_startproc` 与 `.cfi_endproc` 之间的错误。
- [fricas](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332183512)：文档构建失败，`ht.db` 和 `.pht` 文件未生成。
- [jackett](https://github.com/happyendingll/intel-bottles/actions/runs/34775066010/job/103798616407)：构建 `dotnet@9` 依赖时，VB/C# compiler server 关闭失败。
- [libtensorflow](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988872684)：Bazel 请求 runner 上不存在的 `macosx10.11` SDK。
- [logstash](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988873380)：Gradle bootstrap 报 `BUILD FAILED`；保留的日志没有展开根因。
- [mpv](https://github.com/happyendingll/intel-bottles/actions/runs/35382450939/job/105765889356)：无效的 `stolendata-mpv` Cask 定义阻断安装。
- [mycli](https://github.com/happyendingll/intel-bottles/actions/runs/34754920248/job/103738930739)：job 在约 1 小时 49 分后取消，历史日志不可用，不能断定为一小时构建超时。
- [openldap](https://github.com/happyendingll/intel-bottles/actions/runs/34775066010/job/103798616417)：Formula 的 `inreplace` 步骤失败。
- [powershell](https://github.com/happyendingll/intel-bottles/actions/runs/34775066010/job/103798616466)：出现 `dotnet` 符号链接冲突，随后 `dotnet restore` 失败；日志不足以证明两者的直接因果关系。
- [skip](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988879009)：job 记录为失败，但 GitHub 日志返回 `BlobNotFound`，无法确认原因。
- [wxpython](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093078626)：代码生成阶段缺少 `wxGLAttribsBase` 的 XML 文件。

## 3. 依赖要求 arm64（7）

这些包的依赖 graalvm、podman 或 mlx 等明确要求 Apple Silicon，当前 Intel runner 无法满足。

[astra](https://github.com/happyendingll/intel-bottles/actions/runs/35437021616/job/105881407050)、[astro](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856965524)、[cljfmt](https://github.com/happyendingll/intel-bottles/actions/runs/34930853524/job/104313226484)、[crip](https://github.com/happyendingll/intel-bottles/actions/runs/35067144987/job/104700194162)、[mlx-lm](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856969124)、[rapid-mlx](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093074702)、[signal-cli](https://github.com/happyendingll/intel-bottles/actions/runs/34775066010/job/103798616434)。

## 4. 缺构建工具、模块或头文件（6）

- `libusb.h` 缺失：[far2l-tty](https://github.com/happyendingll/intel-bottles/actions/runs/35437021616/job/105881407619)、[gammu](https://github.com/happyendingll/intel-bottles/actions/runs/35470174882/job/105969704123)、[libsidplayfp](https://github.com/happyendingll/intel-bottles/actions/runs/35437021616/job/105881408957)。
- 缺所需 libcurl 或 pkg-config：[freeswitch](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093067715)。
- 缺 Perl `URI::Escape`：[kdoctools](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332185922)。
- 缺 `git-lfs`：[odin](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856969799)。

## 5. Formula 安装或链接冲突（5）

- 冲突的已安装 Formula：[bazel](https://github.com/happyendingll/intel-bottles/actions/runs/35067144987/job/104700194130)、[bazel-diff](https://github.com/happyendingll/intel-bottles/actions/runs/34930853524/job/104313226030)。
- `dotnet` 可执行文件链接冲突：[garnet](https://github.com/happyendingll/intel-bottles/actions/runs/35067144987/job/104700196419)、[kiota](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332186034)。`kiota` 后续的 `dotnet publish` 也退出 1，不能仅凭日志确认两者因果关系。
- 与 runner 已安装的 yq 都提供 `yq` 命令：[python-yq](https://github.com/happyendingll/intel-bottles/actions/runs/35706692167/job/106677569263)。

## 6. 要求完整 Xcode.app（4）

日志要求完整 Xcode 26；只有 Command Line Tools 不足以构建。

[asccli](https://github.com/happyendingll/intel-bottles/actions/runs/35706692167/job/106677559746)、[cdo](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093064373)、[draw-things-cli](https://github.com/happyendingll/intel-bottles/actions/runs/35437021616/job/105881407564)、[vapor](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988881433)。

## 7. 网络解析失败或下载长期无响应（4）

- `rubygems.org` DNS 解析失败：[jrsonnet](https://github.com/happyendingll/intel-bottles/actions/runs/35706692167/job/106677563821)。
- Git 获取超时：[librealsense](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093070426)。
- `brew fetch` 连续两次超过 1,200 秒，随后触及 job 时限；日志未指出具体站点：[scotch](https://github.com/happyendingll/intel-bottles/actions/runs/34977393656/job/104408844449)。
- RubyGems 获取 gemspec 失败：[sequoia-sq](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332191582)。

## 8. 下载源返回 HTTP 错误（3）

- 源码地址返回 404：[asdf](https://github.com/happyendingll/intel-bottles/actions/runs/35802884488/job/106997247465)、[ocm](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332189260)。
- 补丁地址返回 500：[coccinelle](https://github.com/happyendingll/intel-bottles/actions/runs/35533179699/job/106137682399)。

## 9. 下载内容 SHA256 不符（3）

[opencrabs](https://github.com/happyendingll/intel-bottles/actions/runs/35533179699/job/106137686638)、[ratify](https://github.com/happyendingll/intel-bottles/actions/runs/35533179699/job/106137687304)、[rosa-cli](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093075293)。这些包重试后仍提示下载内容与 Formula 声明的校验值不符。

## 10. 编译后上传 Artifact 失败（3）

[ecflow-ui](https://github.com/happyendingll/intel-bottles/actions/runs/35067144987/job/104700195383)、[kimi-code](https://github.com/happyendingll/intel-bottles/actions/runs/35356297416/job/105636713483)、[postgrest](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988876932)。构建后的 GitHub Artifact 上传分别出现请求超时或 `ENOTFOUND`；不应归咎于源码编译。

## 11. 编译器不支持 `_Float16`（2）

[fizz](https://github.com/happyendingll/intel-bottles/actions/runs/35382450939/job/105807657873)、[folly](https://github.com/happyendingll/intel-bottles/actions/runs/35382450939/job/105765887834)：均报告 `_Float16 is not supported on this target`。
