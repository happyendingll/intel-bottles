# 预热失败原因归档（更新于 2026-10-16）

本报告最初逐一核对 2026-09-23 当日 [`prewarm-failures.txt`](../prewarm-failures.txt) 中的 94 个 Formula，依据历史 `warm-bottles` job 日志归类。2026-09-28～29 的三次手动补编（[第一批](https://github.com/happyendingll/intel-bottles/actions/runs/36398508359)、[第二批](https://github.com/happyendingll/intel-bottles/actions/runs/36435197899)、[第三批](https://github.com/happyendingll/intel-bottles/actions/runs/36532738876)）覆盖原“约 60 分钟达到 job 上限”的 43 个包：其中 39 个构建 job 成功，已从本失败报告和当前隔离文件移除；余下 4 个依据新日志重新归类，留下 55 个历史记录。

2026-10-15 更新：核对[自动编译链路报告 issue](https://github.com/happyendingll/intel-bottles/issues/2) 中 2026-09-22 起的“新增失败或超时”，按要求排除 2026-10-09 那次报告。其余报告共列出 35 个不同的新增项：5 个已经在下文，30 个此前未归档。其中 `nift` 后来手动补编成功并移出隔离文件，本次不再加入；其余 29 个依据各自的 warm build job 日志加入，当时合计 84 个历史记录。

2026-10-16 更新：[最近一次手动 build-bottles](https://github.com/happyendingll/intel-bottles/actions/runs/38706697355) 指定重试 9 个包。`aptos`、`gerbil-scheme`、`julia`、`nushell`、`mcp-atlassian`、`vite-plus`、`scipy` 的 bottle 均在 [wave0 发布 job](https://github.com/happyendingll/intel-bottles/actions/runs/38706697355/job/116539517082) 中验证、上传，并将 bottle 配置推送到 Homebrew fork；`mapproxy` 已有同版本 bottle，本次判定无需重建。这 8 个包从失败归档移除。`mlkit` 重试失败，按新日志重新归类。现存 76 个历史失败记录。每个包只计入一个类别；类别沿用原报告顺序。包名链接直达对应 GitHub Actions job。

这是历史失败记录，不表示 Formula 现在仍缺官方 bottle，也不表示下次重试必然失败。尤其是接近 60 分钟被取消的 job，日志没有证明其源码无法编译；网络故障和 GitHub Artifact 上传故障也应与源码编译错误区分。日志不可用或输出不足时，明确标为无法确认。

| 类别 | 包数 |
|---|---:|
| 其他：独有原因或证据不足 | 23 |
| 依赖或构建组件不支持 Intel | 10 |
| 缺少或版本不符的构建工具、模块或头文件 | 7 |
| Formula 安装或链接冲突 | 5 |
| 网络连接、解析或 TLS 校验失败 | 8 |
| 要求完整 Xcode.app | 5 |
| 下载源返回 HTTP 错误 | 4 |
| 下载内容 SHA256 不符 | 5 |
| 编译后上传 Artifact 失败 | 5 |
| 编译器不支持 `_Float16` | 2 |
| 接近 6 小时被取消，未见编译错误 | 2 |
| 约 60 分钟达到 job 上限 | 0 |
| **合计** | **76** |

## 1. 其他：独有原因或证据不足（23）

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
- [magika](https://github.com/happyendingll/intel-bottles/actions/runs/36145982275/job/108107642884)、[bkmr](https://github.com/happyendingll/intel-bottles/actions/runs/36353990178/job/108718201148)：两者都在编译依赖 `onnxruntime` 1.30.0 时，于 CMake 约 20% 处报 `make: *** [all] Error 2`；主日志只附上末尾 15 行，没有显示最初的编译错误，不能把 `ranlib` 的“no symbols”警告直接当作根因。
- [sapling](https://github.com/happyendingll/intel-bottles/actions/runs/36993032606/job/110794186192)：构建期间 `git ls-remote --tags` 查询 `watchman` 仓库连续两次退出 128，但主日志没有提供 Git 的具体错误；同时出现 Xcode 缓存写入被拒绝和 Python 链接冲突，无法确认哪项导致最终失败。
- [pocket-tts](https://github.com/happyendingll/intel-bottles/actions/runs/36825948985/job/110251997681)：第一次安装在生成 Bash 补全时，`pocket-tts --show-completion bash` 以 `ABRT` 终止；再次安装约 60 分钟时被取消。日志不足以解释进程为何中止。
- [torchvision](https://github.com/happyendingll/intel-bottles/actions/runs/36825948985/job/110251998918)：CMake 编译和安装完成，随后 pip 生成 `pyproject.toml` 元数据的子进程以 `-6` 退出；日志提示没有更多输出。
- [cmake-docs](https://github.com/happyendingll/intel-bottles/actions/runs/37198923782/job/111426573596)：下载自建 `cmake` bottle 曾返回 HTTP 500；重试后 `cmake-docs` 报告构建完成，但 `brew install` 最终仍退出 1，主日志未给出最终退出原因，也没有生成 bottle。
- [r](https://github.com/happyendingll/intel-bottles/actions/runs/37198923782/job/111426575145)：`r-app` Cask 定义调用了不支持的 `on_catalina`，尚未进入源码编译。
- [unisonlang](https://github.com/happyendingll/intel-bottles/actions/runs/37198923782/job/111426576011)：Formula 安装过程两次抛出 `NameError: uninitialized constant ...::Timeout`。

## 2. 依赖或构建组件不支持 Intel（10）

这些包的源码、依赖或构建组件要求 Apple Silicon，或缺少 Intel macOS 所需的原生二进制，当前 Intel runner 无法满足。

[astra](https://github.com/happyendingll/intel-bottles/actions/runs/35437021616/job/105881407050)、[astro](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856965524)、[cljfmt](https://github.com/happyendingll/intel-bottles/actions/runs/34930853524/job/104313226484)、[crip](https://github.com/happyendingll/intel-bottles/actions/runs/35067144987/job/104700194162)、[mlx-lm](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856969124)、[rapid-mlx](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093074702)、[signal-cli](https://github.com/happyendingll/intel-bottles/actions/runs/34775066010/job/103798616434)。

- [podman-compose](https://github.com/happyendingll/intel-bottles/actions/runs/38370103518/job/115205129693)：安装依赖 `podman` 时，Formula 明确要求 arm64。
- [teleport](https://github.com/happyendingll/intel-bottles/actions/runs/37198923782/job/111426575863)：构建 Web 资源时，`@pnpm/exe@11.20.0` 报告没有 `darwin-x64` 原生二进制。
- [mlkit](https://github.com/happyendingll/intel-bottles/actions/runs/38706697355/job/116415532401)：手动补编两次均在 `./configure` 阶段报 `macOS requires Apple Silicon and a native arm64 shell`，没有进入源码编译。

## 3. 缺少或版本不符的构建工具、模块或头文件（7）

- `libusb.h` 缺失：[far2l-tty](https://github.com/happyendingll/intel-bottles/actions/runs/35437021616/job/105881407619)、[gammu](https://github.com/happyendingll/intel-bottles/actions/runs/35470174882/job/105969704123)、[libsidplayfp](https://github.com/happyendingll/intel-bottles/actions/runs/35437021616/job/105881408957)。
- 缺所需 libcurl 或 pkg-config：[freeswitch](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093067715)。
- 缺 Perl `URI::Escape`：[kdoctools](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332185922)。
- 缺 `git-lfs`：[odin](https://github.com/happyendingll/intel-bottles/actions/runs/34805622247/job/103856969799)。
- Swift tools 版本不足：[peekaboo](https://github.com/happyendingll/intel-bottles/actions/runs/38370103518/job/115205129450) 的源码要求 6.2.0，runner 上安装的是 6.1.0；三次尝试均在 Swift 包解析时失败。

## 4. Formula 安装或链接冲突（5）

- 冲突的已安装 Formula：[bazel](https://github.com/happyendingll/intel-bottles/actions/runs/35067144987/job/104700194130)、[bazel-diff](https://github.com/happyendingll/intel-bottles/actions/runs/34930853524/job/104313226030)。
- `dotnet` 可执行文件链接冲突：[garnet](https://github.com/happyendingll/intel-bottles/actions/runs/35067144987/job/104700196419)、[kiota](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332186034)。`kiota` 后续的 `dotnet publish` 也退出 1，不能仅凭日志确认两者因果关系。
- 与 runner 已安装的 yq 都提供 `yq` 命令：[python-yq](https://github.com/happyendingll/intel-bottles/actions/runs/35706692167/job/106677569263)。

## 5. 网络连接、解析或 TLS 校验失败（8）

- `rubygems.org` DNS 解析失败：[jrsonnet](https://github.com/happyendingll/intel-bottles/actions/runs/35706692167/job/106677563821)。
- Git 获取超时：[librealsense](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093070426)。
- [mesheryctl](https://github.com/happyendingll/intel-bottles/actions/runs/36532738876/job/109290158859)：手动补编时 `brew fetch` 连续三次各超过 1,200 秒，最终报无法下载源码；日志未给出具体下载站点。
- `brew fetch` 连续两次超过 1,200 秒，随后触及 job 时限；日志未指出具体站点：[scotch](https://github.com/happyendingll/intel-bottles/actions/runs/34977393656/job/104408844449)。
- RubyGems 获取 gemspec 失败：[sequoia-sq](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332191582)。
- Go 模块代理请求超时：[kuttl](https://github.com/happyendingll/intel-bottles/actions/runs/35929804537/job/107413817207) 在两次安装中均无法从 `proxy.golang.org` 获取依赖，日志同时出现 DNS 与 TCP 连接超时。
- 源码站点 TLS 证书校验失败：[bigloo](https://github.com/happyendingll/intel-bottles/actions/runs/36274012017/job/108493320242) 的下载站证书无法通过校验；[algol68g](https://github.com/happyendingll/intel-bottles/actions/runs/38247113449/job/114804380732) 的证书主机名与 `algol68genie.nl` 不符。各自重试三次后仍无法下载。

## 6. 要求完整 Xcode.app（5）

日志要求完整 Xcode 26；只有 Command Line Tools 不足以构建。

[asccli](https://github.com/happyendingll/intel-bottles/actions/runs/35706692167/job/106677559746)、[cdo](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093064373)、[draw-things-cli](https://github.com/happyendingll/intel-bottles/actions/runs/35437021616/job/105881407564)、[vapor](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988881433)、[vroom](https://github.com/happyendingll/intel-bottles/actions/runs/35929804537/job/107413821517)。`vroom` 在两次安装中都明确要求完整 Xcode 26.0。

## 7. 下载源返回 HTTP 错误（4）

- 源码地址返回 404：[asdf](https://github.com/happyendingll/intel-bottles/actions/runs/35802884488/job/106997247465)、[ocm](https://github.com/happyendingll/intel-bottles/actions/runs/34954087202/job/104332189260)。
- 补丁地址返回 500：[coccinelle](https://github.com/happyendingll/intel-bottles/actions/runs/35533179699/job/106137682399)。
- 源码标签归档地址连续返回 404：[pinboard-notes-backup](https://github.com/happyendingll/intel-bottles/actions/runs/37248097045/job/111570129147)。

## 8. 下载内容 SHA256 不符（5）

[opencrabs](https://github.com/happyendingll/intel-bottles/actions/runs/35533179699/job/106137686638)、[ratify](https://github.com/happyendingll/intel-bottles/actions/runs/35533179699/job/106137687304)、[rosa-cli](https://github.com/happyendingll/intel-bottles/actions/runs/34878878555/job/104093075293)。这些包重试后仍提示下载内容与 Formula 声明的校验值不符。

[findent](https://github.com/happyendingll/intel-bottles/actions/runs/36274012017/job/108493320220)、[wcslib](https://github.com/happyendingll/intel-bottles/actions/runs/36353990178/job/108718202131)：源码下载均连续三次报告相同的 SHA256 不匹配。

## 9. 编译后上传 Artifact 失败（5）

[ecflow-ui](https://github.com/happyendingll/intel-bottles/actions/runs/35067144987/job/104700195383)、[kimi-code](https://github.com/happyendingll/intel-bottles/actions/runs/35356297416/job/105636713483)、[postgrest](https://github.com/happyendingll/intel-bottles/actions/runs/34848024979/job/103988876932)。构建后的 GitHub Artifact 上传分别出现请求超时或 `ENOTFOUND`；不应归咎于源码编译。

[pgrx](https://github.com/happyendingll/intel-bottles/actions/runs/36516822746/job/109241095682)、[detect-secrets](https://github.com/happyendingll/intel-bottles/actions/runs/36993032606/job/110794181961)：各自已生成 bottle 文件，上传 Artifact 时分别报 `ETIMEDOUT`、`ENOTFOUND`。

## 10. 编译器不支持 `_Float16`（2）

[fizz](https://github.com/happyendingll/intel-bottles/actions/runs/35382450939/job/105807657873)、[folly](https://github.com/happyendingll/intel-bottles/actions/runs/35382450939/job/105765887834)：均报告 `_Float16 is not supported on this target`。

## 11. 接近 6 小时被取消，未见编译错误（2）

- [graph-tool](https://github.com/happyendingll/intel-bottles/actions/runs/36532738876/job/109290158886)：手动补编已进入 `make install`，约 5 小时 49 分后 job 被取消；主日志未显示源码编译错误。
- [swift](https://github.com/happyendingll/intel-bottles/actions/runs/36532738876/job/109290161974)：手动补编已运行 `swift/utils/build-script`，约 5 小时 49 分后 job 被取消；主日志未显示源码编译错误。

两项都接近 GitHub 托管 runner 的 6 小时上限，但日志仅能确认“被取消”，不能据此断言源码无法编译。

## 12. 约 60 分钟达到 job 上限（0）

原有 43 项中，39 项的手动补编 job 成功，余下 4 项已依据新日志移至上述类别。2026-10-15 手动重试前，本分类另有 9 项：7 项完成 bottle 发布，`mapproxy` 已有同版本 bottle，`mlkit` 则确认不支持 Intel 并移至第 2 类。本分类暂时没有未解决项；单次超时本身不能证明源码编译失败。
