# GitSonar 战略演进最终版

**版本**：Final Strategy Draft  
**日期**：2026-04-22  
**定位**：Windows 本地优先的 GitHub 开源项目情报工作台

---

## 0. 核心结论

GitSonar 下一阶段最重要的目标不是“做更多 GitHub 榜单”，也不是立刻把技术栈全部重写，而是把当前已经成型的 **发现 → 整理 → 跟踪 → 判断** 工作流升级成一个稳定、可扩展、可解释、可长期积累的本地情报系统。

最终建议采用这条路线：

```text
短期：补齐知识管理和更新研判
  ↓
中期：拆分 API、迁移 SQLite、引入真实事件流
  ↓
长期：内嵌本地 AI、语义聚类、仓库地图、多设备加密同步
```

也就是说：

> **先把 GitSonar 从“趋势暂存器”做成“开源项目研判台”，再逐步演进成“AI 驱动的本地开源情报中枢”。**

---

## 1. 对两版建议的综合评判

### 1.1 应该采纳的方向

你原始项目已经具备非常清晰的产品闭环：

```text
发现 GitHub 项目
  → 标记状态
  → 长期跟踪
  → 对比分析
  → 辅助判断
```

这一点是 GitSonar 最有价值的地方。它不是 GitHub Trending 的桌面镜像，而是把“发现之后怎么处理”变成了本地工作流。

两版建议中，最值得合并的方向是：

| 方向 | 采纳程度 | 最终判断 |
|---|---:|---|
| **内嵌 AI 研判** | 高 | 必须做，但先做结构化 AI Insight，不要先做复杂 Agent |
| **更新中心升级** | 高 | 必须做，变化日志要升级为 Update Inbox |
| **保存发现视角** | 高 | 必须做，这是从一次搜索变成长期情报源的关键 |
| **标签 / 集合 / 笔记 / 决策记录** | 高 | 必须做，四态系统不够支撑长期积累 |
| **SQLite 迁移** | 高 | 必须做，但要在状态模型扩展后进行 |
| **SSE 实时事件流** | 高 | 适合 GitSonar，优先于 WebSocket |
| **FastAPI / ASGI 化** | 中高 | 建议做，但不应作为第一步大重写 |
| **React / Vite 前端重构** | 中 | 可做，但不是 MVP 必需项 |
| **仓库语义聚类 / 地图** | 中高 | 很有价值，但应先做列表聚类，再做 WebGL 地图 |
| **本地 RAG / Docling** | 中 | 方向正确，但 Gemini 方案偏重，应该后置 |
| **PyInstaller 误报缓解 / 代码签名** | 中 | 发布阶段重要，但不是产品主线 |
| **Gist 同步** | 低到中 | 只能做加密备份，不应把 secret gist 当真正私有存储 |

---

### 1.2 Gemini 内容里需要修正的地方

Gemini 的报告视野很大，补充了架构、发布、安全、可视化等维度，但有几处需要降温处理：

#### 1.2.1 不要四条战线同时推进

Gemini 建议“FastAPI + React + SSE + 本地 RAG + WebGL 图谱 + 多维分类”同时推进。这个方案方向没错，但工程风险很高。

更稳妥的顺序是：

```text
1. 数据模型和产品闭环先变强
2. 再拆 API 和存储
3. 再做 AI 和语义聚类
4. 最后考虑完整前端框架迁移
```

原因很简单：如果先重写前端和 HTTP 服务，而产品模型还没定，后续标签、集合、AI artifact、更新事件都会反复改接口。

#### 1.2.2 FastAPI 不能自动解决所有并发问题

FastAPI 支持 `async def` 路由，适合 I/O 密集型 API 服务。[^fastapi-async]  
但如果底层 GitHub 请求仍然使用同步 `requests`，只是把 `http.server` 换成 FastAPI，收益有限。

真正要做的是：

```text
HTTP 服务 API-first
  + 后端 Job 模型
  + async httpx 或受控线程池
  + SSE 事件推送
  + 请求预算和限流
```

因此，FastAPI 是架构升级的一部分，不是单独的灵丹妙药。

#### 1.2.3 GIL 不是当前最大瓶颈

当前 GitSonar 的主要问题不是 Python GIL 本身，而是：

- 整体 HTML 重新生成；
- 全局状态和多把锁耦合较强；
- 前端靠轮询感知后端变化；
- 任务、进度、状态、缓存没有统一事件模型；
- GitHub API 请求预算和条件缓存不足。

GitHub 请求、翻译、详情抓取都是 I/O 密集型任务。对这类场景，锁粒度、任务队列、缓存策略、API 预算通常比 GIL 更关键。

#### 1.2.4 Docling / RAG 不应作为第一阶段 AI 核心

仓库 README、description、topics、release note、issue 摘要已经足够做第一版 AI 研判。

第一阶段不需要上复杂文档解析和 RAG。更合理的是：

```text
RepoContext 构建
  → README 结构化截断
  → 输出 JSON Schema
  → 缓存 AI Artifact
```

等到你要分析大型文档、PDF、架构说明、长 release note 时，再引入更强的文档摄取管道。

#### 1.2.5 Secret Gist 不等于私有存储

GitHub 官方文档明确说明：secret gist 不会出现在 Discover，也不容易被搜索到，但它不是严格意义上的私有内容；知道链接的人可以访问。[^github-gist-secret]

因此，多设备同步可以支持 GitHub Gist，但必须满足：

```text
仅上传客户端加密后的密文
  + 用户明确知道 secret gist 不是私有仓库
  + 默认推荐 private repo / WebDAV / 本地备份
```

#### 1.2.6 本地翻译模型可以做，但不能影响开箱体验

Gemini 提到 HY-MT1.5-1.8B 这类本地翻译模型。它确实是一个值得关注的方向，HY-MT1.5 官方仓库提供 1.8B、7B、FP8、Int4、GGUF 等模型版本，并主打多语种翻译与边缘部署。[^hymt]

但它不适合成为默认路径。原因是：

- 模型下载成本高；
- 用户首次启动会被复杂配置打断；
- GitSonar 的第一痛点不是“翻译模型强不强”，而是“发现查询是否可解释、可保存、可迭代”。

更合理的策略是：

```text
默认：内置术语词典 + 可编辑 Query Normalizer
增强：Google / 其他在线翻译 provider
高级：local model runner 挂载本地翻译模型
```

---

## 2. 最终产品定位

### 2.1 一句话定位

> **GitSonar 是一个本地隐私优先的 GitHub 开源项目情报工作台，帮助用户发现项目、组织线索、持续跟踪变化，并形成技术判断。**

### 2.2 不应该成为的东西

GitSonar 不应该优先变成：

- GitHub Trending 桌面镜像；
- 普通书签管理器；
- GitHub 客户端替代品；
- 大而全的协作平台；
- 云端 SaaS；
- AI 聊天壳。

### 2.3 应该成为的东西

GitSonar 应该成为：

```text
开源项目雷达
  + 本地知识库
  + 更新收件箱
  + 技术选型辅助台
  + AI 研判缓存层
```

核心体验应该是：

```text
我发现了一批项目
  → GitSonar 帮我分组、排序、解释原因
  → 我标记、备注、收藏、忽略
  → GitSonar 持续跟踪重要变化
  → AI 帮我总结“这个变化是否值得关注”
  → 我形成笔记、标签和决策
```

---

## 3. 总体演进原则

### 3.1 不做大重写，做分层替换

当前架构虽然有局限，但已经跑通了：

- Windows 桌面；
- WebView / 浏览器前端；
- 本地 HTTP API；
- GitHub Trending 抓取；
- 关键词发现；
- 四态状态；
- 收藏追踪；
- GitHub Stars 同步；
- ChatGPT 提示词交接；
- DPAPI Token 加密。

所以不要推倒重来。

建议遵循：

```text
先抽象接口
再替换实现
先稳定数据模型
再重构 UI
先结构化输出
再引入复杂 AI
```

### 3.2 AI 只能降低判断成本，不能替用户做最终决定

GitSonar 的可信度来自“用户可控”。

AI 应该提供：

- 摘要；
- 风险提示；
- 推荐理由；
- 对比维度；
- 标签建议；
- 下一步动作建议。

AI 不应该默认自动：

- 关注仓库；
- 忽略仓库；
- 删除笔记；
- 改用户标签；
- 做最终采用决策。

正确模式是：

```text
AI 建议
  → 用户确认
  → 写入状态 / 标签 / 集合 / 决策
```

### 3.3 本地优先，但允许用户主动选择云增强

默认策略：

```text
无 AI 也可完整使用
本地 AI 优先
云端 AI 必须显式 opt-in
发送前必须可预览字段
所有 AI 输出必须可缓存、可删除、可重新生成
```

### 3.4 所有排序都必须可解释

用户必须知道为什么一个项目排在前面。

每个结果卡片应该能展开：

```text
为什么推荐：
- description 命中 desktop automation
- topics 命中 automation / windows
- 最近 14 天有 push
- star 增长高于同组项目
- 与你关注的 owner/repo 语义相似
```

---

## 4. 推荐路线图

### 4.1 总览

| 阶段 | 目标 | 核心成果 | 不做什么 |
|---|---|---|---|
| **Phase 1** | 产品闭环增强 | 标签、笔记、保存发现视角、Update Inbox、诊断中心 | 不重写前端 |
| **Phase 2** | 数据和 API 稳定 | 静态壳 + JSON API、SQLite、Job/Event 模型、SSE | 不急着上 React |
| **Phase 3** | AI 内嵌 | Repo Insight、批量归类、更新摘要、AI Artifact | 不做复杂 Agent |
| **Phase 4** | 语义发现 | 聚类分组、相似仓库、仓库地图、反馈学习 | 不先做 3D 炫技 |
| **Phase 5** | 发布和同步 | 加密备份、多设备同步、代码签名、安装体验 | 不做中心化账号系统 |

---

### 4.2 下一版最建议落地的功能组合

下一版建议不要只做单个功能，而是做一个最小闭环：

```text
保存发现视角
  → 运行关键词发现
  → 结果显示推荐原因
  → 用户批量标记
  → 标签 / 笔记沉淀
  → 关注仓库进入 Update Inbox
  → 更新可读、可忽略、可置顶
```

对应 P0 功能：

| 功能 | 最小实现 |
|---|---|
| **保存发现视角** | 保存 query、filters、rank_mode、auto_expand、last_run |
| **标签** | 用户标签 + 系统标签，先不做复杂层级 |
| **笔记** | 每个 repo 一段 Markdown note |
| **Update Inbox** | read / dismiss / pin / priority_score |
| **推荐原因** | 展示 discovery score 的中间依据 |
| **网络诊断** | GitHub API、Token、代理、端口、状态文件权限 |
| **导出 Markdown** | 单仓库 / 批量仓库摘要可复制 |

---

## 5. AI 深度集成最终方案

### 5.1 不做聊天框，做研判流水线

不要把 AI 功能做成普通聊天窗口。

GitSonar 更适合的 AI 结构是：

```text
GitHub 原始数据
  → RepoContext / UpdateContext / CompareContext
  → 隐私过滤
  → AI Provider
  → 结构化 JSON 输出
  → AI Artifact 缓存
  → 前端卡片 / 抽屉 / 更新中心渲染
```

### 5.2 AI Provider 分层

建议新增目录：

```text
src/gitsonar/runtime_ai/
├── providers.py
├── local_provider.py
├── openai_compatible.py
├── prompt_registry.py
├── context_builder.py
├── privacy.py
├── artifacts.py
└── schemas.py
```

Provider 接口：

```python
class AIProvider:
    name: str

    def analyze_repo(self, context: RepoContext) -> RepoInsight:
        ...

    def triage_repos(self, context: BatchTriageContext) -> BatchTriageResult:
        ...

    def summarize_updates(self, context: UpdateContext) -> UpdateDigest:
        ...

    def compare_repos(self, context: CompareContext) -> CompareInsight:
        ...
```

### 5.3 AI 模式

| 模式 | 行为 | 适合人群 |
|---|---|---|
| **关闭 AI** | 只保留当前提示词交接 | 不想用 AI 的用户 |
| **提示词交接** | 生成可复制 Prompt | 轻量用户 |
| **本地 AI** | local model runner / LocalAI / OpenAI-compatible localhost | 隐私敏感用户 |
| **云端 AI** | 用户主动配置 API Key | 追求效果的用户 |

local model runner 提供本地 HTTP API，默认可通过本机服务调用 `/api/chat` 等端点；这很适合 GitSonar 的本地优先定位。[^ollama-api]

### 5.4 第一个 AI 功能：Repo Insight

不要先做 AI Agent。第一版只做仓库研判卡。

#### 输入：RepoContext

```json
{
  "repo": "owner/name",
  "description": "...",
  "topics": ["..."],
  "language": "Python",
  "stars": 12000,
  "forks": 800,
  "created_at": "...",
  "pushed_at": "...",
  "latest_release": "...",
  "readme_summary": "...",
  "user_state": "watching",
  "known_similar_repos": ["owner/another"]
}
```

#### 输出：RepoInsight

```json
{
  "one_line_judgement": "...",
  "best_for": ["..."],
  "not_good_for": ["..."],
  "learning_value": ["..."],
  "risk_signals": ["..."],
  "next_actions": ["..."],
  "suggested_tags": ["..."],
  "confidence": 0.72
}
```

#### UI 展示

```text
AI Insight

一句话判断：
这个项目适合用来快速搭建 xxx，但不适合作为长期基础设施依赖。

适合场景：
- ...

风险信号：
- ...

下一步：
- 先看 examples/
- 对比 owner/a 和 owner/b
```

### 5.5 第二个 AI 功能：批量归类

关键词发现结果出来后，增加：

```text
[AI 批量归类]
```

输出：

| 分组 | 仓库 | 建议动作 |
|---|---|---|
| 可直接试用 | A、B、C | 关注 |
| 值得学习架构 | D、E | 待看 |
| 只适合观察 | F、G | 加入集合 |
| 噪声 / 可忽略 | H、I | 忽略 |

用户可以一键确认：

```text
[关注整组] [待看整组] [忽略整组] [加标签]
```

### 5.6 第三个 AI 功能：更新摘要

Update Inbox 中每条重要更新可以生成摘要：

```json
{
  "repo": "owner/name",
  "event_type": "major_release",
  "previous": {
    "version": "1.9.0",
    "stars": 1200
  },
  "current": {
    "version": "2.0.0",
    "stars": 1680
  },
  "release_note_excerpt": "..."
}
```

输出：

```json
{
  "summary": "该版本重构了插件系统，并废弃旧配置格式。",
  "impact": "如果你关注的是桌面集成，需要重新检查 examples。",
  "priority_reason": "major release + breaking change",
  "recommended_action": "优先查看"
}
```

### 5.7 AI Artifact 缓存

必须保存 AI 输出的来源和版本：

```json
{
  "id": "uuid",
  "repo_url": "https://github.com/owner/name",
  "artifact_type": "repo_insight",
  "provider": "ollama",
  "model": "qwen-or-mistral",
  "prompt_version": "repo_insight_v1",
  "input_hash": "...",
  "output_json": {},
  "created_at": "...",
  "source_snapshot_id": "..."
}
```

原则：

- 同样输入不重复调用；
- 模型、提示词、输入 hash 都要记录；
- 用户能删除、重新生成；
- 云端模式必须显示“本次会发送哪些字段”。

---

## 6. 发现体验升级最终方案

### 6.1 从一次性搜索变成 Discovery View

新增概念：**发现视角**。

```json
{
  "id": "uuid",
  "name": "Python 桌面自动化",
  "query_original": "桌面自动化",
  "query_normalized": ["desktop automation", "ui automation", "rpa"],
  "languages": ["Python"],
  "rank_mode": "balanced",
  "auto_expand": true,
  "negative_keywords": ["demo", "toy", "awesome"],
  "min_stars": 100,
  "last_run_at": "...",
  "last_result_count": 82
}
```

UI：

```text
发现视角
- AI Agent 框架
- Python 桌面自动化
- SQLite 工具
- 开源竞品监控
```

每个视角支持：

- 重新运行；
- 查看新增结果；
- 查看已忽略结果；
- 对比上次结果；
- 固定到首页；
- 导出 JSON / Markdown。

### 6.2 Query Normalizer 替代单一翻译

当前中文关键词依赖公共 Google Translate，稳定性和技术术语准确性都不可控。

建议改成：

```text
QueryNormalizer
  → 原词保留
  → 英文翻译
  → 技术词典扩展
  → 同义词扩展
  → 负关键词建议
  → 用户确认
```

内置词典示例：

```json
{
  "桌面自动化": ["desktop automation", "UI automation", "RPA"],
  "知识库": ["knowledge base", "personal knowledge management", "PKM"],
  "向量数据库": ["vector database", "embedding search", "semantic search"]
}
```

发现任务开始前展示：

```text
原始关键词：桌面自动化
查询扩展：
- desktop automation
- UI automation
- RPA

负关键词：
- toy
- demo
- awesome
```

用户可以勾选或删除。

### 6.3 发现结果分层展示

不要只显示线性卡片列表。

建议四层结构：

```text
总览层：这批结果是什么结构
  ↓
聚类层：有哪些主题组
  ↓
列表层：每个仓库具体是什么
  ↓
动作层：关注 / 待看 / 忽略 / 加标签 / 加集合
```

示例：

```text
本次发现 126 个候选，分为 7 个主题：

1. Desktop automation framework      28 个
2. Browser control / RPA             21 个
3. Windows UI automation             18 个
4. Cross-platform GUI tools          15 个
5. Testing helpers                   13 个
6. Low-code automation               12 个
7. Noise / weak match                19 个
```

### 6.4 聚类路线

先做简单聚类，不要一开始做复杂 3D 图谱。

#### MVP

```text
TF-IDF
  + cosine similarity
  + KMeans / Agglomerative
  + 自动生成组名
```

#### P1

```text
Embedding
  + cosine similarity
  + KMeans / HDBSCAN
  + 相似项目推荐
```

#### P2

```text
Embedding
  + UMAP / t-SNE 降维
  + WebGL 仓库地图
```

仓库向量文本：

```text
repo name
description
topics
language
readme_summary
```

### 6.5 仓库地图

仓库地图不要作为第一版核心功能，但可以作为 P1/P2 的亮点。

推荐交互：

```text
左侧：聚类列表
中间：二维地图
右侧：仓库详情抽屉
```

点的含义：

| 视觉变量 | 含义 |
|---|---|
| 点大小 | stars |
| 点边框 | 用户状态 |
| 点分组颜色 | 聚类主题 |
| 点透明度 | 最近活跃程度 |
| 连线 | 语义相似 / 同主题 / 同集合 |

如果前端仍是 Vanilla JS，可以先做二维 Canvas。  
如果迁移 React，可以考虑 Sigma.js、Reagraph 等 WebGL 图谱库。

### 6.6 Ranking 透明化

卡片上显示：

```text
综合分 82
相关性 90 | 热度 74 | 新鲜度 68 | 成熟度 81
```

展开：

```text
命中原因：
- description 命中 "desktop automation"
- topics 命中 "windows", "automation"
- README 提到 "control UI elements"
- 最近 30 天有 commit
```

### 6.7 Ranking 数学增强

Gemini 提到的 Wilson Score 和时间衰减值得采纳，但应该谨慎落地。

#### Balanced 模式

适合引入 Wilson 下界，减少小样本极端值误导。

可用于：

- issue close ratio；
- fork/star ratio；
- release stability；
- recent activity reliability。

#### Hot / Trend 模式

适合引入时间衰减：

```text
hot_score =
  log10(recent_star_delta + recent_fork_delta + 1)
  × recency_decay
  × relevance_factor
```

原则：

- 不能只看绝对 star；
- 不能让新项目凭 10 stars 轻易碾压成熟项目；
- 必须展示排序解释。

---

## 7. Update Inbox 最终方案

### 7.1 从变化日志升级为更新收件箱

当前 favorite_updates 是“变化记录”。下一步应该变成：

```text
Update Inbox
  = 更新事件
  + 优先级
  + 已读 / 忽略 / 置顶
  + 自上次查看以来
  + AI 摘要
```

### 7.2 更新事件模型

```json
{
  "id": "uuid",
  "repo_url": "https://github.com/owner/name",
  "event_type": "major_release",
  "event_level": "high",
  "priority_score": 86,
  "title": "Released v2.0.0",
  "summary": "...",
  "raw_delta": {},
  "first_seen_at": "...",
  "last_seen_at": "...",
  "read_at": null,
  "dismissed_at": null,
  "snoozed_until": null,
  "pinned": false
}
```

### 7.3 事件类型

| 类型 | 默认优先级 | 说明 |
|---|---:|---|
| `major_release` | 高 | 大版本发布 |
| `minor_release` | 中 | 小版本发布 |
| `patch_release` | 低 | 补丁发布 |
| `star_spike` | 中 / 高 | 短期增长明显 |
| `activity_resume` | 中 | 沉寂后恢复活跃 |
| `archived` | 高 | 仓库归档 |
| `license_changed` | 高 | License 改变 |
| `readme_changed` | 中 | README 大幅变化 |
| `topic_changed` | 低 | topics 改变 |
| `repo_renamed` | 高 | 仓库改名或迁移 |

### 7.4 优先级评分

```text
priority_score =
  repo_importance * 0.35
+ event_importance * 0.30
+ novelty * 0.15
+ user_topic_match * 0.10
+ recency * 0.10
- noise_penalty
```

### 7.5 信息层级

Gemini 的 Tier 思路值得采纳，但建议用更容易理解的命名：

| 层级 | 名称 | 说明 | 默认行为 |
|---|---|---|---|
| L0 | 关键依赖 | 正在使用或计划采用 | 高优先级展示 |
| L1 | 战略观察 | 竞品、候选技术、重点趋势 | 按日 / 周聚合 |
| L2 | 兴趣收藏 | 学习、灵感、资料 | 默认折叠 |

### 7.6 “自上次查看以来”

每个 repo 保存：

```json
{
  "last_opened_at": "...",
  "last_update_reviewed_at": "..."
}
```

详情页显示：

```text
自你上次查看以来：

- 新增 2 个 release
- star +430
- README 有明显变化
- 最近一次 push：2026-04-21
- AI 判断：项目正在从 demo 走向可用阶段
```

### 7.7 GitHub API 消耗优化

GitHub REST API 未认证请求有较低的主限额，认证请求限额更高。[^github-rate-limits]  
GitHub 官方也建议优先使用认证请求，并避免不必要轮询；对于桌面本地应用，无法自然接收 GitHub Webhook 时，应使用更强缓存、条件请求和请求预算。[^github-best-practices]

建议新增：

```json
{
  "repo_url": "...",
  "etag_repo": "...",
  "etag_releases": "...",
  "last_modified_repo": "...",
  "last_modified_releases": "...",
  "last_checked_at": "..."
}
```

请求策略：

| 仓库状态 | 检查频率 |
|---|---|
| L0 关键依赖 | 高频 |
| L1 战略观察 | 正常 |
| L2 兴趣收藏 | 低频 |
| 已读但未关注 | 极低频 |
| 忽略 | 不检查 |

---

## 8. 状态系统最终方案

### 8.1 从四态扩展为多维知识系统

当前四态：

```text
关注 / 待看 / 已读 / 忽略
```

应该保留，但不够。

最终模型：

```text
status：流程状态
tags：主题和属性
collections：研究任务
notes：个人笔记
decision：判断结论
rating：主观价值
priority：更新层级
```

### 8.2 新字段

```json
{
  "status": "watching",
  "tags": ["desktop", "automation", "competitor"],
  "collections": ["桌面 AI 助手竞品研究"],
  "note": "可借鉴它的插件机制。",
  "rating": 4,
  "decision": "trial",
  "decision_reason": "文档完整，近期活跃，适合做 PoC。",
  "priority": "L1",
  "pinned": false,
  "last_reviewed_at": "..."
}
```

### 8.3 标签类型

| 类型 | 来源 | 示例 |
|---|---|---|
| 用户标签 | 用户手动创建 | `竞品`, `可借鉴UI`, `学习资料` |
| 系统标签 | 规则生成 | `recently-active`, `has-release` |
| AI 标签 | AI 建议 | `agent-framework`, `desktop-helper` |

AI 标签必须先显示为“建议”，用户确认后才写入。

### 8.4 集合 Collections

集合不是标签。标签描述属性，集合描述任务。

示例：

```text
集合：桌面 AI 助手竞品研究

包含：
- repo A
- repo B
- repo C
- 对比记录
- 用户笔记
- AI 总结
- 最终决策
```

集合详情页：

```text
集合摘要
- 共 18 个仓库
- 5 个重点关注
- 3 个近期有重要更新
- 2 个建议优先阅读
```

### 8.5 决策记录

技术选型用户非常需要这个功能。

```json
{
  "repo_url": "...",
  "decision": "trial",
  "reason": "文档完整，近期活跃，适合作为 PoC。",
  "risks": ["核心维护者少", "Windows 支持不明确"],
  "next_step": "本周跑 examples。",
  "created_at": "...",
  "updated_at": "..."
}
```

UI：

```text
[采用] [试用] [学习] [暂缓] [放弃]
```

---

## 9. 架构演进最终方案

### 9.1 当前架构的真实问题

当前架构的问题不是“不能用”，而是扩展到 AI、标签、更新中心、聚类后会变难维护。

核心问题：

| 问题 | 影响 |
|---|---|
| 整体 HTML 重新生成 | 局部更新困难，刷新体验不顺 |
| UI 和数据耦合 | 每次数据变化都牵动模板 |
| JSON 状态文件变重 | 标签、笔记、事件、AI 输出难维护 |
| 轮询任务进度 | 实时性和一致性不足 |
| 全局状态锁多 | 并发任务复杂度上升 |
| API 边界不稳定 | 前端和后端难独立演进 |

### 9.2 阶段一：静态壳 + JSON API

先不重写技术栈，只改渲染边界。

```text
index.html 静态壳
  ↓
前端 JS 加载数据
  ↓
GET /api/bootstrap
GET /api/repos?view=today
GET /api/repos?view=favorites
GET /api/updates
GET /api/discovery/views
```

新增 API：

```text
GET  /api/bootstrap
GET  /api/repos
GET  /api/repos/{owner}/{name}
GET  /api/updates
GET  /api/discovery/views
POST /api/discovery/views
GET  /api/tags
POST /api/tags
GET  /api/collections
POST /api/collections
```

收益：

- 不再每次重建大 HTML；
- 前端状态可保留；
- UI 可局部刷新；
- 后续迁移 React 更容易。

### 9.3 阶段二：SQLite 迁移

当加入标签、集合、笔记、事件、AI artifact 后，JSON 会变成瓶颈。

建议迁移 SQLite。

SQLite FTS5 支持全文检索和 BM25 排名，可以用于仓库描述、README 摘要、笔记、集合说明的本地搜索。[^sqlite-fts5]

核心表：

```sql
repos
repo_snapshots
user_repo_state
tags
repo_tags
collections
collection_repos
notes
update_events
discovery_views
discovery_runs
discovery_results
ai_artifacts
settings_kv
```

迁移策略：

```text
启动时检测 user_state.json
  ↓
如果没有 gitsonar.db
  ↓
导入 JSON
  ↓
生成备份
  ↓
后续仍支持 JSON 导出
```

不要废弃 JSON 导入导出。可携带数据是本地工具的信任基础。

### 9.4 阶段三：Job / Event 模型

统一所有长任务。

```json
{
  "job_id": "uuid",
  "job_type": "discovery",
  "status": "running",
  "progress": 0.42,
  "stage": "auto_expand",
  "message": "正在扩展关键词...",
  "created_at": "...",
  "started_at": "...",
  "finished_at": null,
  "error": null
}
```

覆盖任务：

- 手动刷新；
- 关键词发现；
- 收藏更新；
- GitHub Stars 同步；
- AI 分析；
- 批量归类；
- 导入导出；
- 网络诊断。

API：

```text
POST /api/jobs
GET  /api/jobs/{job_id}
POST /api/jobs/{job_id}/cancel
GET  /api/events/stream
```

### 9.5 阶段四：SSE 事件流

GitSonar 的实时需求主要是后端向前端推送：

- 发现进度；
- 更新事件；
- AI 输出状态；
- 刷新完成；
- 诊断结果。

这非常适合 SSE。浏览器 EventSource 会建立持久连接，并接收 `text/event-stream` 格式的数据。[^mdn-eventsource]  
SSE 的事件流是 UTF-8 文本格式，天然适合推送 JSON 元数据。[^mdn-sse]

事件示例：

```json
{"type": "job.progress", "job_id": "...", "progress": 0.3}
{"type": "repo.updated", "repo_url": "..."}
{"type": "update.created", "event_id": "..."}
{"type": "ai.artifact.created", "artifact_id": "..."}
{"type": "settings.changed"}
```

### 9.6 阶段五：FastAPI / ASGI

完成 API contract、Job 模型、SSE 后，再迁移 FastAPI 最稳。

迁移收益：

- async 路由；
- 自动 OpenAPI 文档；
- 更好的请求校验；
- 更适合 SSE；
- 后续 WebSocket 也容易扩展。

但迁移时要同步处理：

```text
requests → httpx.AsyncClient 或受控线程池
全局变量 → AppState / Repository 层
RLock → 更清晰的事务和队列边界
HTML 模板 → 静态资源
```

### 9.7 WebView2 通信边界

WebView2 支持 Web 页面通过 `postMessage` 将 JSON 可序列化消息异步发送给宿主进程。[^webview2-postmessage]

建议边界：

| 通道 | 用途 |
|---|---|
| HTTP API | 业务数据：repo、状态、发现、更新 |
| SSE | 进度、事件、AI 流式状态 |
| WebView2 postMessage | 窗口控制、托盘、打开文件、系统能力 |

不要把所有业务数据都塞进 WebView2 native bridge。

---

## 10. 安全、发布与同步

### 10.1 DPAPI 继续保留

当前使用 Windows DPAPI 加密 GitHub Token 是正确选择。DPAPI 通常将解密能力绑定到同一用户登录上下文和本机环境。[^dpapi]

建议增强：

```text
Token 不写日志
Token 不进入全局长生命周期变量
仅在构造请求头时短暂解密
异常信息不包含 Authorization header
设置导出不包含明文 Token
```

可以考虑调用 DPAPI 时使用 `CRYPTPROTECT_UI_FORBIDDEN`，避免后台任务意外弹系统 UI。微软文档说明该 flag 用于不允许显示 UI 的场景。[^dpapi]

注意：Python 中“显式覆盖字符串内存”并不可靠。现实做法是缩短明文生命周期、避免日志、避免缓存、避免全局变量。

### 10.2 打包误报处理

PyInstaller 官方文档提到，开发者可能会选择自行构建 bootloader，以避免预编译 bootloader 被广泛使用导致的反病毒误报。[^pyinstaller-bootloader]

建议发布策略：

| 优先级 | 措施 |
|---|---|
| P0 | 保留 zip 便携版，降低安装摩擦 |
| P1 | GitHub Release 提供 SHA256 校验 |
| P1 | 自编译 PyInstaller bootloader |
| P1 | 减少 onefile 解压行为，优先 onedir |
| P2 | 代码签名证书 |
| P2 | 评估 Nuitka / embedded Python |
| P2 | 自动化 VirusTotal 预检，但不要把它作为唯一判断 |

### 10.3 多设备同步

不建议做中心化账号系统。

可选方案：

| 方案 | 推荐度 | 说明 |
|---|---:|---|
| 本地导出 / 导入 | 高 | 必须保留 |
| WebDAV 加密同步 | 高 | 适合隐私用户 |
| 私有 Git 仓库加密同步 | 高 | 适合开发者 |
| Secret Gist 加密同步 | 中 | 只能上传密文，并提示 secret gist 不是私有 |
| 自建云账号 | 低 | 复杂度高，偏离本地优先定位 |

同步内容：

```text
gitsonar.db encrypted backup
settings excluding token
discovery views
tags
collections
notes
ai artifacts optional
```

不要同步：

- 明文 GitHub Token；
- 临时缓存；
- 未脱敏诊断日志；
- 用户未确认的 AI 发送内容。

---

## 11. 网络诊断中心

### 11.1 为什么是 P0

GitSonar 强依赖：

- GitHub API；
- GitHub Trending HTML；
- GitHub Token；
- 代理；
- 本地端口；
- WebView2；
- DPAPI；
- 本地状态文件。

一旦失败，用户很难判断原因。

### 11.2 一键诊断项

```text
设置 → 诊断 → 一键检查
```

检查：

| 检查项 | 内容 |
|---|---|
| GitHub API | api.github.com 是否可达 |
| GitHub Trending | trending 页面是否可访问和解析 |
| Token 有效性 | /user 是否返回正常 |
| Rate Limit | 当前剩余额度 |
| Search API | 搜索接口是否可用 |
| 代理 | HTTP / HTTPS 代理是否生效 |
| 本地端口 | 8080 是否被占用 |
| WebView2 Runtime | 是否可启动 |
| 状态文件权限 | db / json 是否可读写 |
| DPAPI | Token 加解密是否正常 |
| 翻译服务 | 当前 provider 是否可用 |
| local model runner | localhost:11434 是否可达 |

### 11.3 输出格式

不要只给错误，要给原因和建议：

```text
GitHub Token 无效

可能原因：
1. Token 已过期
2. Token 权限不足
3. 代理拦截请求

建议：
- 重新生成 fine-grained token
- 检查系统代理
- 点击“复制诊断报告”
```

诊断报告应自动脱敏：

```text
Authorization: Bearer ghp_****abcd
```

---

## 12. 首次使用引导

### 12.1 不要先让用户配置一堆东西

第一次启动不要先要求：

- 配 Token；
- 配模型；
- 配代理；
- 读说明文档。

应该让用户马上看到价值。

### 12.2 目标选择

```text
你主要想用 GitSonar 做什么？

[ ] 技术选型
[ ] 学习开源项目
[ ] 竞品观察
[ ] 跟踪 AI / 开发工具趋势
[ ] 管理我已经 star 的仓库
```

根据选择调整默认首页：

| 目标 | 默认强化 |
|---|---|
| 技术选型 | license、release、维护活跃度、风险 |
| 学习项目 | README、examples、学习价值 |
| 竞品观察 | 集合、更新中心、对比 |
| 趋势跟踪 | star 增长、近期活跃、hot score |
| 管理 Stars | 引导配置 Token 和导入 stars |

### 12.3 Quick Win

引导用户完成一次完整闭环：

```text
搜索一个关键词
  → 保存发现视角
  → 关注一个仓库
  → 加标签
  → 写一句笔记
  → 查看 Update Inbox
```

---

## 13. 数据模型建议

### 13.1 repos

```sql
CREATE TABLE repos (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    owner TEXT NOT NULL,
    name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    html_url TEXT NOT NULL,
    description TEXT,
    language TEXT,
    topics_json TEXT,
    created_at TEXT,
    pushed_at TEXT,
    archived INTEGER DEFAULT 0,
    disabled INTEGER DEFAULT 0,
    last_seen_at TEXT
);
```

### 13.2 repo_snapshots

```sql
CREATE TABLE repo_snapshots (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    stars INTEGER,
    forks INTEGER,
    open_issues INTEGER,
    watchers INTEGER,
    default_branch TEXT,
    latest_release TEXT,
    readme_summary TEXT,
    raw_json TEXT,
    captured_at TEXT NOT NULL
);
```

### 13.3 user_repo_state

```sql
CREATE TABLE user_repo_state (
    repo_id INTEGER PRIMARY KEY,
    status TEXT,
    priority TEXT,
    rating INTEGER,
    note TEXT,
    decision TEXT,
    decision_reason TEXT,
    pinned INTEGER DEFAULT 0,
    last_opened_at TEXT,
    last_reviewed_at TEXT
);
```

### 13.4 tags

```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL
);
```

```sql
CREATE TABLE repo_tags (
    repo_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (repo_id, tag_id)
);
```

### 13.5 collections

```sql
CREATE TABLE collections (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL
);
```

```sql
CREATE TABLE collection_repos (
    collection_id INTEGER NOT NULL,
    repo_id INTEGER NOT NULL,
    note TEXT,
    sort_order INTEGER,
    PRIMARY KEY (collection_id, repo_id)
);
```

### 13.6 update_events

```sql
CREATE TABLE update_events (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    priority_score REAL DEFAULT 0,
    title TEXT NOT NULL,
    summary TEXT,
    raw_delta_json TEXT,
    first_seen_at TEXT NOT NULL,
    read_at TEXT,
    dismissed_at TEXT,
    pinned INTEGER DEFAULT 0
);
```

### 13.7 ai_artifacts

```sql
CREATE TABLE ai_artifacts (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER,
    artifact_type TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    output_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

### 13.8 discovery_views

```sql
CREATE TABLE discovery_views (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    query_original TEXT NOT NULL,
    query_normalized_json TEXT,
    filters_json TEXT,
    rank_mode TEXT,
    auto_expand INTEGER DEFAULT 1,
    negative_keywords_json TEXT,
    created_at TEXT NOT NULL,
    last_run_at TEXT
);
```

---

## 14. API 设计建议

### 14.1 Bootstrap

```text
GET /api/bootstrap
```

返回：

```json
{
  "app": {},
  "settings": {},
  "views": [],
  "counts": {},
  "capabilities": {
    "ai": false,
    "ollama": false,
    "github_token": true
  }
}
```

### 14.2 Repos

```text
GET /api/repos?view=today
GET /api/repos?status=watching
GET /api/repos?tag=desktop
GET /api/repos?collection=xxx
GET /api/repos/{owner}/{name}
```

### 14.3 State

```text
POST /api/repos/{owner}/{name}/state
POST /api/repos/batch-state
POST /api/repos/{owner}/{name}/tags
POST /api/repos/{owner}/{name}/note
POST /api/repos/{owner}/{name}/decision
```

### 14.4 Discovery

```text
GET  /api/discovery/views
POST /api/discovery/views
POST /api/discovery/runs
GET  /api/discovery/runs/{id}
POST /api/discovery/runs/{id}/cancel
```

### 14.5 Updates

```text
GET  /api/updates
POST /api/updates/{id}/read
POST /api/updates/{id}/dismiss
POST /api/updates/{id}/pin
POST /api/updates/check
```

### 14.6 AI

```text
GET  /api/ai/providers
POST /api/ai/repo-insight
POST /api/ai/batch-triage
POST /api/ai/update-digest
POST /api/ai/compare
GET  /api/ai/artifacts/{id}
DELETE /api/ai/artifacts/{id}
```

### 14.7 Events

```text
GET /api/events/stream
```

---

## 15. 前端 UX 建议

### 15.1 首页改成“今日需要处理什么”

不要默认只打开 Trending。

首页展示：

```text
今日建议处理

高优先级更新：3
新的发现结果：18
待看超过 7 天：12
需要复查的关注项目：5
```

### 15.2 卡片信息层级

```text
第一眼：
repo name / description / language / stars / status

第二眼：
score breakdown / topics / last active / release

第三眼：
AI insight / update summary / notes / actions
```

### 15.3 详情抽屉分 Tab

```text
[概览] [README] [更新] [AI Insight] [笔记] [相似项目]
```

### 15.4 批量操作 Dock

```text
批量操作：
[关注] [待看] [已读] [忽略]
[加标签] [加入集合] [AI 批量归类] [导出选中]
```

选中多个仓库时展示统计：

```text
已选 12 个仓库
语言：Python 7 / TypeScript 3 / Rust 2
状态：未处理 9 / 待看 3
平均 star：3.2k
```

### 15.5 忽略原因

点击忽略时显示：

```text
忽略原因：
[不相关] [太旧] [只是 demo] [已有替代] [质量不高] [其他]
```

这些数据反向优化发现排名。

### 15.6 关注理由

点击关注时可选：

```text
为什么关注？
[技术选型] [学习架构] [竞品观察] [产品灵感] [稍后阅读]
```

---

## 16. 不建议优先做的方向

| 方向 | 原因 |
|---|---|
| 完整协作系统 | 会把本地工具复杂化 |
| 中心化账号体系 | 运维成本高，偏离本地优先 |
| 直接 Electron 重写 | 现有 Python + WebView 路线够用 |
| 一开始做 3D 图谱 | 好看但不一定提升判断效率 |
| 复杂 AI Agent | 不稳定，难解释，成本高 |
| 把 ChatGPT 网页嵌进应用 | 仍然不是工作流内嵌 |
| 默认下载大模型 | 损害首次启动体验 |
| Secret Gist 明文同步 | 安全风险高 |

---

## 17. P0 / P1 / P2 优先级清单

### P0：下一版必须优先做

| 功能 | 价值 | 风险 |
|---|---|---|
| 保存发现视角 | 从一次搜索变长期追踪 | 低 |
| 标签 | 解决仓库组织问题 | 低 |
| 笔记 | 沉淀判断依据 | 低 |
| Update Inbox | 降低更新噪音 | 中 |
| 推荐原因 | 提升排序信任 | 低 |
| 网络诊断 | 降低失败挫败感 | 低 |
| 复制 Markdown 摘要 | 提升外部工作流兼容 | 低 |

### P1：架构和智能化核心

| 功能 | 价值 | 风险 |
|---|---|---|
| 静态壳 + JSON API | 降低模板耦合 | 中 |
| SQLite | 支撑长期数据 | 中 |
| Job/Event 模型 | 统一后台任务 | 中 |
| SSE | 实时进度与更新 | 中 |
| Repo Insight | AI 进入工作流 | 中 |
| AI Artifact 缓存 | AI 可追溯 | 中 |
| 发现结果聚类 | 降低认知负担 | 中 |

### P2：增强和差异化

| 功能 | 价值 | 风险 |
|---|---|---|
| WebGL 仓库地图 | 视觉差异化 | 中高 |
| 本地翻译模型 | 离线能力 | 中高 |
| 加密同步 | 多设备使用 | 中 |
| PyInstaller 误报缓解 | 发布体验 | 中 |
| 代码签名 | 信任建设 | 中高 |
| 私有 repo / WebDAV 同步 | 长期可靠 | 中 |
| React / Vite 重构 | 前端长期维护 | 中高 |

---

## 18. 最终推荐的下一步实施顺序

### 第一步：产品闭环增强

先实现：

```text
Discovery View
Tags
Notes
Update Inbox v1
Diagnostics
推荐原因展示
```

这一步可以继续沿用当前 WebView + 本地 HTTP + Vanilla JS，不需要大重构。

### 第二步：数据模型升级

做：

```text
SQLite
JSON 导入
JSON 导出
状态迁移
更新事件表
标签 / 集合表
```

### 第三步：API-first

做：

```text
index.html 静态壳
/api/bootstrap
/api/repos
/api/updates
/api/discovery/views
局部渲染
```

### 第四步：Job/Event/SSE

做：

```text
统一后台任务
进度事件
更新事件
AI 事件
SSE 长连接
```

### 第五步：AI Insight

做：

```text
local model runner 探测
Provider 抽象
RepoContext
RepoInsight JSON Schema
AI Artifact 缓存
隐私预览
```

### 第六步：语义发现

做：

```text
TF-IDF 聚类
Embedding 可选
相似项目推荐
仓库地图 MVP
```

---

## 19. 最终架构草图

```text
Windows Shell / Tray
        │
        ▼
WebView2 / Browser
        │
        ├── Static HTML/CSS/JS
        ├── REST API calls
        └── SSE EventSource
        │
        ▼
Local API Server
        │
        ├── Repo API
        ├── Discovery API
        ├── Update API
        ├── State API
        ├── AI API
        └── Diagnostics API
        │
        ▼
Application Services
        │
        ├── DiscoveryService
        ├── UpdateInboxService
        ├── RepoStateService
        ├── AIInsightService
        ├── GitHubSyncService
        └── DiagnosticsService
        │
        ▼
Storage
        │
        ├── SQLite
        ├── Detail Cache
        ├── AI Artifacts
        ├── Export JSON
        └── Encrypted Backup
        │
        ▼
External / Local Providers
        ├── GitHub REST API
        ├── GitHub Trending HTML
        ├── local model runner / LocalAI
        ├── Translation Provider
        └── WebDAV / Private Git Remote
```

---

## 20. 最终一句话建议

GitSonar 的正确演进路线是：

> **用标签、笔记、集合、Update Inbox 先把“发现之后的管理”做扎实；再用 API-first、SQLite、SSE 把架构拆稳；最后用本地 AI 和语义聚类把“判断成本”降下来。**

不要把下一版做成“大重写”。  
下一版应该做成“GitSonar 真正开始像一个情报工作台”。

---

## 参考资料

[^fastapi-async]: FastAPI 官方文档，Concurrency and async / await：https://fastapi.tiangolo.com/async/
[^mdn-eventsource]: MDN，EventSource：https://developer.mozilla.org/en-US/docs/Web/API/EventSource
[^mdn-sse]: MDN，Using server-sent events：https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
[^github-rate-limits]: GitHub Docs，Rate limits for the REST API：https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
[^github-best-practices]: GitHub Docs，Best practices for using the REST API：https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
[^ollama-api]: local model runner API 文档，Generate a chat message：https://docs.ollama.com/api/chat
[^sqlite-fts5]: SQLite 官方文档，FTS5 Extension：https://www.sqlite.org/fts5.html
[^dpapi]: Microsoft Learn，CryptProtectData function：https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata
[^pyinstaller-bootloader]: PyInstaller 官方文档，Building the Bootloader：https://pyinstaller.org/en/latest/bootloader-building.html
[^webview2-postmessage]: Microsoft Edge WebView2 JavaScript API，WebView postMessage：https://learn.microsoft.com/en-us/microsoft-edge/webview2/reference/javascript/webview
[^github-gist-secret]: GitHub Docs，Creating gists：https://docs.github.com/articles/creating-gists
[^hymt]: Tencent-Hunyuan/HY-MT GitHub 仓库：https://github.com/Tencent-Hunyuan/HY-MT
