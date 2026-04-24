# 发布加固与 AV 误报缓解计划

## 任务元信息

- 任务 ID：`GS-P2-004`
- 优先级：`P2`
- 当前状态：`[x]`
- Sprint 候选排名：`10`
- 推荐 commit message：`chore: add release checksum manifest`

## 标题

`发布加固与 AV 误报缓解`

## 摘要

- 这个任务为发布产物增加本地校验清单，并记录 AV / SmartScreen 风险的低风险缓解路径。
- 现在做是因为核心产品闭环和 P1 API / event / 聚类边界已经稳定，可以开始补发布可信度基础设施。
- 做完后维护者可以在本地生成 `release-manifest.json` 和 `SHA256SUMS.txt`，用户可用哈希校验下载文件。

## 战略映射

- 战略文档：
  - `docs/strategy/GITSONAR_STRATEGY.md`
- 路线图文档：
  - `docs/roadmap/ROADMAP.md`
- 对应 Sprint 队列：
  - `docs/sprints/CURRENT_TOP10.md`
- 当前状态参考：
  - `docs/ARCHITECTURE.md`
  - `docs/SECURITY.md`

## 当前状态

- 当前行为：`scripts/build_exe.ps1` 生成 PyInstaller onefile EXE，`scripts/build_setup.ps1` 生成 Inno Setup 安装器。
- 当前技术形态：Windows-first PowerShell packaging scripts。
- 已知痛点：发布产物缺少标准校验清单；README 已明确当前无自动更新和代码签名。
- 现有约束：不能要求证书、外部账号、VirusTotal API、签名密钥或改变默认打包形态。
- 需要检查的文件或区域：
  - `scripts/build_exe.ps1`
  - `scripts/build_setup.ps1`
  - `packaging/GitSonar.iss`
  - `README.md`
  - `docs/SECURITY.md`

## 目标

- 主要目标：新增可重复运行的本地 release checksum manifest 脚本。
- 次要目标：记录 AV / SmartScreen 缓解的安全边界和后续步骤。
- 成功标准：
  - 脚本可对 EXE 和 installer 生成 SHA256 清单。
  - 脚本支持测试用临时 `-DistRoot`。
  - 没有网络请求、签名操作或构建模式变更。
  - 自动化测试覆盖清单生成。

## 非目标

- 不切换 PyInstaller `onefile` / `onedir` 默认策略。
- 不申请或使用代码签名证书。
- 不调用 VirusTotal、GitHub Release API 或其他云服务。
- 不发布、不上传、不 push。

## 用户影响

- 普通用户暂时无 UI 变化。
- 发布者可以随 release 附带 SHA256 信息。
- 用户下载后可通过哈希更明确地确认产物完整性。

## 隐私与显式同意

- 不涉及 AI、云 API、同步、Token 或用户数据。
- 没有数据离开本机。
- 不需要 opt-in。
- 不处理密钥或证书。

## 范围

### 范围内

- 新增 `scripts/write_release_manifest.ps1`。
- 新增脚本测试。
- 新增计划和追踪记录。

### 范围外

- 改打包模式。
- 代码签名。
- 外部信誉扫描。
- Release 上传自动化。

## 架构触点

- 涉及的运行时模块：无。
- HTTP / API 变更：无。
- 状态 / 持久化变更：无。
- UI 变更：无。
- 后台任务变更：无。
- 打包 / 启动 / 壳层变更：新增 release manifest 辅助脚本，不改变现有 build scripts。

## 数据模型

- 新字段：无。
- 新文件或新表：无。
- 迁移需求：无。
- 导入 / 导出影响：无。

## API 与契约

- 要新增或修改的端点：无。
- 请求 / 响应结构：无。
- 错误行为：没有可识别 release artifact 时脚本输出提示并成功退出，便于在未构建环境中安全运行。
- 兼容性说明：不改变现有 build output 路径。

## 执行步骤

1. 第一步：写失败测试。
   预期结果：测试找不到 manifest 脚本或输出文件。
   回滚路径：删除新增测试。
2. 第二步：新增 manifest 脚本。
   预期结果：对指定 `-DistRoot` 下的 `GitSonar.exe` 和 `installer/GitSonarSetup.exe` 生成 JSON 与 SHA256SUMS。
   回滚路径：删除脚本。
3. 第三步：运行测试与手动 dry-run。
   预期结果：测试通过；未构建 artifacts 时 dry-run 安全退出。
   回滚路径：回退脚本和测试。

## 风险

- 技术风险：不同 PowerShell 版本 JSON 编码表现略有差异。
- 产品风险：哈希清单只证明完整性，不等同代码签名信誉。
- 隐私 / 安全风险：低；只读取本地 release artifact 文件。
- 发布风险：低；不改变打包产物生成流程。

## 验证

- 单元测试：
  - `python -m pytest tests/test_release_manifest_script.py -q`
- 集成测试：
  - `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\write_release_manifest.ps1 -DryRun`
- 手动检查：
  - 检查生成清单字段包含 path、size、sha256。
- 性能或可靠性检查：
  - 只处理固定 release artifact 文件，耗时与文件大小线性相关。
- 需要关注的日志 / 诊断信号：
  - 无新增应用日志。

## 发布与回滚

- 如何增量发布？发布前在 build 后运行 manifest 脚本并附带输出文件。
- 是否需要开关或受控状态？不需要。
- 如果失败，用户如何恢复？不运行脚本即可恢复旧发布流程。

## 文档更新

- 需要更新的文档：`TASKS.md`、`docs/sprints/CURRENT_TOP10.md`、`docs/progress/PROGRESS.md`
- 需要更新的用户可见文案：无。
- 需要更新的内部维护说明：本计划文件。

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[x]` | 已新增本地 release manifest 脚本并完成验证。 |
| `2026-04-24` | `[~]` | 已创建计划并开始 TDD。 |

## 验证记录

- 已运行测试：
  - `python -m pytest tests/test_release_manifest_script.py -q`，1 passed。
  - `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\write_release_manifest.ps1 -DryRun`，成功输出当前 `GitSonar.exe` 与 `installer/GitSonarSetup.exe` 的 SHA256 manifest。
- 手动验证：确认脚本只读取指定 `-DistRoot` 下的本地 release artifacts；`-DryRun` 不写入文件；无网络调用、签名操作或打包模式变更。
- 尚未覆盖的缺口：未运行真实发布上传流程；未处理代码签名和 AV 信誉扫描，后者需要证书或外部服务决策。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
