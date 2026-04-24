# GS-P1-011 DPAPI UI Forbidden Security Hardening

## 任务元信息

- 任务 ID：`GS-P1-011`
- 优先级：`P1`
- 当前状态：`[x]`
- Sprint 候选排名：Project Autopilot Safe Loop / Security hardening
- 推荐 commit message：`fix(security): forbid dpapi ui prompts`
- Commit / PR：`fix(security): forbid dpapi ui prompts`

## 标题

`DPAPI 加解密禁止后台 UI`

## 摘要

- 这个任务要解决什么问题？当前 DPAPI 调用 flags 为 `0`，后台保存或读取 Token / 代理密文时没有显式禁止系统 UI。
- 为什么现在做？上一批安全加固已完成用户可见脱敏，本任务继续补一个小范围、低风险的本地凭据保护细节。
- 做完后用户能看到什么结果？正常情况下 UI 不变化；后台保存或读取密文时更保守，不会要求系统交互 UI。

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

- 当前行为：`encrypt_secret()` 和 `decrypt_secret()` 使用 Windows DPAPI，但 `CryptProtectData` / `CryptUnprotectData` flags 传 `0`。
- 当前技术形态：Python runtime 本地设置层通过 DPAPI 保护 GitHub Token 和含凭据代理 URL。
- 已知痛点：后台任务或无交互场景应避免任何系统 UI。
- 现有约束：不能改变旧 `dpapi:` 密文兼容性；非 Windows 行为保持不变。
- 需要检查的文件或区域：
  - `src/gitsonar/runtime/utils.py`
  - `tests/test_runtime_utils.py`
  - `docs/SECURITY.md`

## 目标

- 主要目标：DPAPI 加密和解密都传入 `CRYPTPROTECT_UI_FORBIDDEN`。
- 次要目标：用测试固定 flags，避免后续回退到 `0`。
- 成功标准：聚焦测试通过，旧的加解密入口函数签名和返回格式不变。

## 非目标

- 不迁移已有 `settings.json`。
- 不更换 DPAPI 存储格式。
- 不引入新的密钥管理系统。
- 不修改 Token 或代理设置 UI。

## 用户影响

- 谁会受益？配置 GitHub Token 或代理凭据的 Windows 用户。
- UI 或工作流会发生什么变化？无用户可见 UI 变化。
- 哪些行为保持不变？`dpapi:` 前缀、非 Windows 回退、保存设置和读取设置流程保持不变。

## 隐私与显式同意

- 是否涉及 AI、云 API、同步、Token 或用户数据？涉及本地 Token / 代理密文处理。
- 是否有数据离开本机？没有。
- 是否需要显式 opt-in？不需要，属于本地安全加固。
- 是否需要用户可见的确认或预览？不需要。

## 范围

### 范围内

- 新增 DPAPI flags 常量。
- 修改 `CryptProtectData` 和 `CryptUnprotectData` 调用。
- 新增测试确认 flags 值。
- 更新任务追踪文档和安全文档。

### 范围外

- 不改变 settings JSON schema。
- 不改 GitHub 请求鉴权逻辑。
- 不做跨平台密钥环。

## 架构触点

- 涉及的运行时模块：`runtime/utils.py`
- HTTP / API 变更：无
- 状态 / 持久化变更：无 schema 变更
- UI 变更：无
- 后台任务变更：无
- 打包 / 启动 / 壳层变更：无

## 数据模型

- 新字段：无
- 新文件或新表：无
- 迁移需求：无
- 导入 / 导出影响：无

## API 与契约

- 要新增或修改的端点：无
- 请求 / 响应结构：无
- 错误行为：DPAPI 失败仍沿用当前保守回退。
- 兼容性说明：现有 `dpapi:` 密文仍可解密。

## 执行步骤

1. 第一步：新增失败测试，模拟 Windows DPAPI 并断言 flags 为 `CRYPTPROTECT_UI_FORBIDDEN`。
   预期结果：当前实现传 `0`，测试失败。
   回滚路径：删除新增测试。
2. 第二步：在 `runtime/utils.py` 增加常量并传给加解密 API。
   预期结果：聚焦测试通过。
   回滚路径：恢复 flags 为 `0` 并删除常量。
3. 第三步：更新任务追踪、安全文档和验证记录。
   预期结果：`TASKS.md`、`CURRENT_TOP10.md`、`PROGRESS.md` 与本计划一致。
   回滚路径：撤销对应文档修改。

## 风险

- 技术风险：极低；该 flag 是 DPAPI 标准 flags，不改变密文格式。
- 产品风险：无用户可见功能变化。
- 隐私 / 安全风险：降低后台 UI 交互风险。
- 发布风险：非 Windows 行为仍按原逻辑返回原文或空值。

## 验证

- 单元测试：`python -m pytest tests/test_runtime_utils.py -q`
- 集成测试：`python -m pytest tests/test_runtime_settings.py tests/test_runtime_utils.py -q`
- 手动检查：保存 Token / 代理后重启应用，确认设置仍显示“已配置”。
- 性能或可靠性检查：无额外循环或 I/O。
- 需要关注的日志 / 诊断信号：DPAPI 失败仍不应泄露密文。

## 发布与回滚

- 如何增量发布？随下一版安全加固发布。
- 是否需要开关或受控状态？不需要。
- 如果失败，用户如何恢复？回滚本次代码；旧密文格式不变。

## 文档更新

- 需要更新的文档：
  - `TASKS.md`
  - `docs/sprints/CURRENT_TOP10.md`
  - `docs/progress/PROGRESS.md`
  - `docs/SECURITY.md`
- 需要更新的用户可见文案：无
- 需要更新的内部维护说明：本计划验证记录

## 进度记录

| 日期 | 状态 | 备注 |
|---|---|---|
| `2026-04-24` | `[~]` | 已创建计划，准备按 TDD 添加 DPAPI flags 测试。 |
| `2026-04-24` | `[x]` | 已完成 DPAPI flags 加固，聚焦测试和设置层回归测试通过。 |

## 验证记录

- 已运行测试：
  - RED：`python -m pytest tests/test_runtime_utils.py::RuntimeUtilsTests::test_dpapi_encrypt_and_decrypt_forbid_system_ui -q`，失败原因是 DPAPI flags 仍为 `0`。
  - GREEN：`python -m pytest tests/test_runtime_utils.py::RuntimeUtilsTests::test_dpapi_encrypt_and_decrypt_forbid_system_ui -q`，1 passed。
  - Focused：`python -m pytest tests/test_runtime_utils.py -q`，4 passed。
  - Regression：`python -m pytest tests/test_runtime_settings.py tests/test_runtime_utils.py -q`，14 passed。
- 手动验证：保存 GitHub Token 或含凭据代理 URL，重启应用后打开设置，确认显示“已配置”且无系统交互弹窗。
- 尚未覆盖的缺口：真实 Windows DPAPI 弹窗行为无法在单元测试中直接观察，已通过 flags 断言覆盖调用契约。

## 验收清单

- [x] 范围小且可回滚
- [x] 没有隐藏的大迁移
- [x] 隐私 / opt-in 行为明确
- [x] 回滚路径已定义
- [x] 验证步骤具体可执行
- [x] 已写明战略与路线图映射
