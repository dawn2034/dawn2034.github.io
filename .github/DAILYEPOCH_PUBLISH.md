# DailyEpoch 发布操作协议

版本：2026-10-13。写作标准继续使用 `DailyEpoch/CONTENT_GUIDE.md`；本文件规定提交、发布和故障分类。不得通过降低内容标准解决写入故障。

## 授权与能力检查

每次执行先发现当前 GitHub 工具，确认是否实际提供文件/对象/分支写入动作。不要把过去会话的能力状态当作今天的事实。用户的仓库权限、应用许可、当前工具能力分别核对。若没有写入动作，明确写“当前执行环境未提供写入工具”，不捏造一次写入失败。权限/安全拒绝不可改走别的接口规避；保留已经获得的原始错误并停止该操作。

## 原子源码提交

1. 读取最新 `master` 提交和 tree，以及最新 `DailyEpoch/index.md`。以 `Asia/Shanghai` 的实际任务执行日期为日报日期，补发保留原日期，禁止沿用上次日期。
2. 正文与聊天中日报完整一致；补发已有原稿时复用原文件 blob，不缩写或重新编造历史内容。发布状态单独报告，不混入历史正文。
3. 将正文和基于最新索引生成的倒序入口放进同一个 tree、同一个 commit。必须保留其余文件。用 `create_tree`/`create_commit`/`update_ref` 时，设置 parent 为刚读取的 master；`force=false`、`expected_sha` 为该 master SHA。
4. 仅当错误明确表示过期 SHA 或 non-fast-forward 时，重新读取 master，对比并重建 tree 和 commit，最多三次。不得盲目将旧恢复分支合并或强推，不得覆盖后来新增的索引入口。
5. 更新成功后重新读取 master：验证文件 SHA/正文完整、标题/日期/文件名/permalink 一致、索引无重复且倒序、公式与代码块完整、没有内部引用标记。创建 blob/commit 或恢复分支均不算正式提交成功。

## 永久触发 PR

源文件验证后再读取 `automation/chirpy-publish` 分支的 `chirpy-src/.dailyepoch-publish-trigger`，取得当前 blob SHA。更新为“实际执行时间、日报日期或补发日期、已验证源码 commit SHA”。始终保留 PR #7 open、unmerged；不合并、不关闭它，不更换 base/head。只允许本仓库该 PR 触发生产发布。

普通日报 Markdown push 不再触发 Chirpy，以免正文、索引和触发文件产生重复构建。配置/主题 push、原有定时与手动触发保留为维护与兜底；日常完成判定仍使用对应 trigger SHA 的 pull_request run。不要把使用 GITHUB_TOKEN 的写入一定会产生后续事件作为假设，必须查到实际运行。

## 构建与发布

`Build and Publish Chirpy` 的生产任务串行排队，不取消正在运行的任务。GitHub concurrency 的 queue:max 最多保留 100 个待运行任务，超量仍可能取消；应控制触发频率。

每次从最新 master 构建，并记录 BUILD_SOURCE_SHA。三个关键步骤名保持为 `Build Chirpy`、`Validate generated site`、`Publish static site to master`。发布前再次获取 master；源码输入若变化，在新快照重新准备/构建/验证，严禁把旧 _site 覆盖到新源码上。纯并发 push 冲突最多安全重试三次；权限、规则、安全拒绝不重试。任何源文件都不属于静态同步可修改范围。

产物必须通过全部日期页存在、源/页数量、索引顺序、canonical、遗留页面、无预览路径及无内部引用标记检查。发布写入 `DailyEpoch/publish-status.json`，记录 source/build/trigger SHA、run URL、时间及每篇原始 Markdown 的 SHA-256；对应提交标题保持 `Publish Chirpy site`。

## 最终验收与错误报告

查找 head_sha 等于本次 trigger commit 的 pull_request run，确认三个关键步骤全部成功；运行中可有限等待、降低轮询频率。然后重新读取 master 的目标 HTML、canonical、发布凭证和新的 Publish Chirpy site 提交，核对 Markdown 哈希和 run 来源。最后可访问公开站点确认 CDN 已同步。

只有上述证据全部通过才写“已发布”。分别报告源码、trigger、构建、静态发布；记录实际 HTTP/工具错误、操作、分支、期望及实际 SHA。不得把 cancelled、permission denied、HTTP 409/422、工具未提供、GitHub 安全拒绝笼统称为“合并失败”。

如本轮无法完成，仍提供完整正文和实际已保存的源码位置；不创建无内容恢复分支，不用替代端点绕过拒绝，不声称稍后会自动完成。本协议不保证未来执行环境的授权永不变化。

## 2026-10-13 补充：具名调用与 PR 三态判定

### 逐步调用与精确断点

优先直接调用当前通过工具发现获得的 GitHub 具名动作。正文 blob、索引 blob、tree、commit、master ref、trigger 文件更新各自独立调用、独立检查返回；不要把它们和动态工具查找、重试逻辑全部包进一个通用代码执行调用。不得引用历史会话中不存在的 `ALL_TOOLS` 或 `tools` 变量。

这不是更改或规避安全检查，而是让每个授权操作可单独验证和定位故障。任一安全/权限拒绝仍须停止。若返回来自执行环境且没有 GitHub HTTP 状态，只能记作执行环境阻断，不能捏造 GitHub 403/409。调用结果因网络超时而未知时，先只读确认是否已成功，不盲目重复写入。

原稿先保存为唯一的 UTF-8 文件，计算 SHA-256 与 Git blob SHA。GitHub 返回的 blob SHA 必须与原文件一致，再进入提交阶段；重试不得通过摘要、截断或人工重新编写全文替代原稿。

### `mergeable` 保留三态，不能强转布尔值

GitHub 原始 PR API 的 `mergeable` 有 `true`、`false`、`null` 三种值。`null` 表示后台尚未算出结果，`mergeable_state: unknown` 同理；它不代表内容冲突。

2026-10-13 本次检查中，简化 PR 工具曾返回 `mergeable: false`，随后原始 `GET /repos/dawn2034/dawn2034.github.io/pulls/7` 返回 `mergeable: null`、`mergeable_state: unknown`，且该 trigger 对应的 PR workflow 已成功。这些响应不能用来证明存在真实冲突，也不能据此回填历史失败根因。

因此：简化工具显示不可合并时，先读取原始 PR 响应。原始值为 null/unknown，则等待后只读复核，不同步分支、不强推、不创建新 PR。只有原始 API 明确判定冲突且对比证据支持，才考虑按用户授权将 master 同步到触发分支；任何时候都不合并 PR #7。

`compare_commits` 的 diverged/ahead/behind 只表示历史关系，不等于文件冲突。PR 返回的 base_sha 也不能代替读取 `master` 当前 ref 来确定源码 parent。

参考：[GitHub Get a pull request：mergeable 三态](https://docs.github.com/en/rest/pulls/pulls#get-a-pull-request)。

### 日期与阶段日志

正常每日运行开始时取得真实时间并转换 Asia/Shanghai，一次性冻结 run_started_at 和 report_date；正文覆盖窗口另写，不能从 UTC 或上一期标题推算日期。补发已有原稿保持其用户指定日期，不将本期改名填补历史缺口。

每轮保留本地审计 JSON，记录正文哈希、源码 commit、trigger commit、实际 workflow、静态验证、原始错误和最近七天的缺稿/缺发布日期。缺少归档不等于调度未运行，最近一次 last_run_time 也不能证明全部历史执行情况。无论某天是否有稿，都不得伪造逐日成功记录。
