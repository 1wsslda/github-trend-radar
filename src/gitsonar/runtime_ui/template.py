#!/usr/bin/env python3
from __future__ import annotations

import json

from .assets import CSS, JS

HTML_HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__APP_NAME__</title>
<style>
"""

HTML_BODY = """</style>
</head>
<body>
<div class="page">
  <header class="workspace-header">
    <div class="workspace-brand">
      <span class="hero-kicker">GitHub Intelligence Desk</span>
      <div class="workspace-title-row">
        <h1 class="workspace-title">__APP_NAME__</h1>
        <div class="workspace-panel-meta">
          <span class="workspace-badge">Reading-first Workspace</span>
          <span class="workspace-panel-summary" id="panel-summary">今日趋势 · 0 个仓库</span>
        </div>
      </div>
    </div>
    <div class="workspace-status">
      <div class="status-card">
        <div class="runtime-note" id="note"></div>
      </div>
      <div class="nav-actions">
        <button class="action-quiet" type="button" onclick="refreshNow()">刷新</button>
        <button class="action-quiet" type="button" onclick="openSettings()">设置</button>
        <div class="menu-wrap" data-menu-id="app-more-menu">
          <button class="action-quiet menu-toggle" type="button" aria-haspopup="menu" aria-expanded="false" onclick="toggleMenu(event,'app-more-menu')">更多<span class="menu-caret"></span></button>
          <div class="menu-panel" id="app-more-menu-panel">
            <button class="menu-item" type="button" onclick="exportUserState();closeMenus();">导出数据</button>
            <button class="menu-item" type="button" onclick="beginImportUserState('merge');closeMenus();">导入并合并</button>
            <button class="menu-item" type="button" onclick="beginImportUserState('replace');closeMenus();">导入并覆盖</button>
            <button class="menu-item" type="button" onclick="syncGitHubStars();closeMenus();">从 GitHub 同步星标</button>
            <button class="menu-item" type="button" id="clear-updates-menu-item" onclick="clearFavoriteUpdates();closeMenus();" hidden>清空关注更新</button>
            <div class="menu-divider"></div>
            <div class="menu-note">快捷键：↑ / ↓ 浏览，Space 选中，Shift + 1~4 批量收纳。</div>
          </div>
        </div>
      </div>
    </div>
  </header>

  <section class="workspace-bar">
    <div class="tabs" id="tabs"></div>
    <div class="workspace-bar-main">
      <div class="workspace-search-wrap">
        <label class="field search-field">
          <span class="field-label">搜索</span>
          <span class="field-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="7"></circle>
              <line x1="20" y1="20" x2="16.65" y2="16.65"></line>
            </svg>
          </span>
          <input id="search" class="field-input" type="search" placeholder="搜索仓库 / 描述 / 语言 / 更新内容" autocomplete="off" autocorrect="off" autocapitalize="none" spellcheck="false">
        </label>
      </div>

      <div class="workspace-summary">
        <div class="summary">可见 <span class="metric-number" id="visible-count">0</span><span id="visible-label"> 个仓库</span></div>
        <div class="sub">已选 <span class="metric-number" id="selected-count">0</span> 项</div>
      </div>

      <div class="action-split menu-wrap" data-menu-id="ai-target-menu">
        <button class="action-primary split-main" id="analyze-visible-btn" type="button" onclick="analyzeVisible()">
          <span class="split-main-label">
            <span class="split-main-title">分析当前列表</span>
            <span class="split-main-note" id="ai-target-label" data-ai-target-label>ChatGPT 网页版</span>
          </span>
        </button>
        <button class="action-primary split-trigger" id="ai-target-trigger" type="button" aria-label="选择分析目标" aria-haspopup="menu" aria-expanded="false" onclick="toggleMenu(event,'ai-target-menu')">
          <span class="menu-caret"></span>
        </button>
        <div class="menu-panel" id="ai-target-menu-panel">
          <button class="menu-item menu-item--check" type="button" data-ai-target="web" onclick="toggleAiTarget('web')">ChatGPT 网页版</button>
          <button class="menu-item menu-item--check" type="button" data-ai-target="desktop" onclick="toggleAiTarget('desktop')">ChatGPT 桌面版</button>
          <button class="menu-item menu-item--check" type="button" data-ai-target="gemini_web" onclick="toggleAiTarget('gemini_web')">Gemini 网页版</button>
          <div class="menu-divider"></div>
          <button class="menu-item menu-item--check" type="button" data-ai-target="copy" onclick="toggleAiTarget('copy')">仅复制提示词</button>
        </div>
      </div>

      <div class="discover-query-row" id="discover-query-row" hidden>
        <div class="discover-query-main">
          <label class="field search-field discover-query-field">
            <span class="field-label">关键词</span>
            <span class="field-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="7"></circle>
                <line x1="20" y1="20" x2="16.65" y2="16.65"></line>
              </svg>
            </span>
            <input id="discover-query" class="field-input" type="search" placeholder="例如 agent / AI agent framework / 图数据库" autocomplete="off" autocorrect="off" autocapitalize="none" spellcheck="false" aria-autocomplete="list" aria-controls="discover-query-suggest" aria-expanded="false">
            <div class="discover-query-suggest" id="discover-query-suggest" hidden></div>
          </label>
          <button class="action-primary" id="discover-run-btn" type="button" onclick="runDiscovery()">开始搜索</button>
        </div>
        <div class="discover-query-support">
          <div class="discover-filter-row">
            <section class="discover-range-card">
              <span class="field-label">结果与扩词</span>
              <div class="discover-range-card-grid">
                <label class="field">
                  <span class="field-label">结果数</span>
                  <input id="discover-limit" class="field-input" type="number" min="5" max="50" step="1">
                </label>
                <label class="checkline checkline--stacked discover-expand-card">
                  <input id="discover-auto-expand" type="checkbox">
                  <span class="checkline-copy">
                    <span class="checkline-title">自动扩词</span>
                    <span class="checkline-note">补充相近表达，优先扩大召回。</span>
                  </span>
                </label>
                <label class="checkline checkline--stacked discover-expand-card">
                  <input id="discover-save-query" type="checkbox">
                  <span class="checkline-copy">
                    <span class="checkline-title">保存本次搜索</span>
                    <span class="checkline-note">保留当前关键词与排序偏好，下次可直接复用。</span>
                  </span>
                </label>
              </div>
            </section>
            <div class="field select-field custom-select discover-ranking-field" data-custom-select-for="discover-ranking-profile" data-menu-id="discover-ranking-profile-menu">
              <span class="field-label">排序方式</span>
              <div class="discover-ranking-field-surface">
                <select id="discover-ranking-profile" class="field-input native-select" aria-hidden="true" tabindex="-1">
                  <option value="balanced">综合排序</option>
                  <option value="hot">热门优先</option>
                  <option value="fresh">新项目优先</option>
                  <option value="builder">实用优先</option>
                  <option value="trend">趋势优先</option>
                </select>
                <button class="field-input select-trigger" id="discover-ranking-profile-trigger" type="button"
                  aria-haspopup="listbox" aria-expanded="false"
                  aria-controls="discover-ranking-profile-menu-panel"
                  onclick="toggleMenu(event,'discover-ranking-profile-menu')">
                  <span class="select-trigger-text">综合排序</span>
                </button>
                <span class="field-meta" id="discover-ranking-profile-meta">平衡相关性、热度与可用性。</span>
              </div>
              <div class="menu-panel select-menu" id="discover-ranking-profile-menu-panel"
                role="listbox" aria-labelledby="discover-ranking-profile-trigger"></div>
            </div>
          </div>
          <div id="discover-saved"></div>
        </div>
      </div>

      <button class="action-quiet workspace-drawer-trigger" id="control-drawer-trigger" type="button" aria-haspopup="dialog" aria-expanded="false" onclick="toggleControlDrawer()">
        <span id="control-drawer-label">筛选</span>
        <span class="menu-caret"></span>
      </button>
    </div>
    <div class="workspace-summary-strip" id="workspace-summary-strip" hidden></div>
    <section class="workspace-drawer" id="control-drawer" hidden>
      <div class="workspace-drawer-head">
        <div>
          <div class="workspace-drawer-title" id="control-drawer-title">筛选</div>
          <div class="sub" id="control-drawer-subtitle">把次级控件直接展开在工作条下方，让仓库列表保持主视角。</div>
        </div>
        <button class="action-quiet compact" type="button" onclick="closeControlDrawer()">收起</button>
      </div>
      <div class="workspace-drawer-body">
        <section class="drawer-section" id="control-drawer-list">
          <div class="control-group" id="state-filter-group">
            <div class="group-label">状态筛选</div>
            <div class="segmented" id="state-filter-seg">
              <button class="seg-btn" type="button" data-value="">全部</button>
              <button class="seg-btn" type="button" data-value="unmarked">未标记</button>
              <button class="seg-btn" type="button" data-value="favorites">收藏</button>
              <button class="seg-btn" type="button" data-value="watch_later">稍后看</button>
              <button class="seg-btn" type="button" data-value="read">已读</button>
              <button class="seg-btn" type="button" data-value="ignored">忽略</button>
            </div>
          </div>

          <div class="field select-field custom-select" data-custom-select-for="language" data-menu-id="language-select-menu">
            <span class="field-label">语言</span>
            <select id="language" class="field-input native-select" aria-hidden="true" tabindex="-1">
              <option value="">全部语言</option>
            </select>
            <button class="field-input select-trigger" id="language-trigger" type="button" aria-haspopup="listbox" aria-expanded="false" aria-controls="language-select-menu-panel" onclick="toggleMenu(event,'language-select-menu')">
              <span class="select-trigger-text">全部语言</span>
            </button>
            <div class="menu-panel select-menu" id="language-select-menu-panel" role="listbox" aria-labelledby="language-trigger"></div>
          </div>

          <div class="control-group" id="sort-primary-group">
            <div class="group-label">排序方式</div>
            <div class="segmented" id="sort-primary-seg">
              <button class="seg-btn" type="button" data-sort-primary="stars">总星标</button>
              <button class="seg-btn" type="button" data-sort-primary="trending">趋势</button>
              <button class="seg-btn" type="button" data-sort-primary="gained">增长</button>
              <div class="menu-wrap" data-menu-id="sort-more-menu">
                <button class="seg-btn" id="sort-more-toggle" type="button" aria-haspopup="menu" aria-expanded="false" onclick="toggleMenu(event,'sort-more-menu')">更多<span class="seg-btn-note" id="sort-more-current"></span><span class="menu-caret"></span></button>
                <div class="menu-panel align-left" id="sort-more-menu-panel">
                  <button class="menu-item" type="button" data-sort-more="forks" onclick="setSortPrimary('forks')">Fork</button>
                  <button class="menu-item" type="button" data-sort-more="name" onclick="setSortPrimary('name')">仓库名</button>
                  <button class="menu-item" type="button" data-sort-more="language" onclick="setSortPrimary('language')">语言</button>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="drawer-section" id="control-drawer-updates" hidden>
          <div class="drawer-note">更新页保持轻量阅读模式。主画布优先展示仓库变化，这里不提供额外筛选；需要清空更新记录时，可在右上角“更多”里处理。</div>
          <div class="drawer-note">快捷键仍可使用：Space 勾选，Shift + 1~4 批量收纳，分析按钮在更新页会保持禁用。</div>
        </section>
      </div>
    </section>
  </section>

  <section class="canvas-intro" id="canvas-intro" hidden></section>
  <div class="cards" id="cards"></div>
</div>

<div class="batch-dock" id="batch-dock">
  <div class="batch-dock-meta">
    <div class="batch-dock-count">
      <span class="batch-dock-label">已选条目</span>
      <span class="batch-dock-value"><span class="metric-number" id="batch-dock-count">0</span> 项</span>
    </div>
  </div>
  <div class="batch-dock-actions">
    <button class="action-primary" type="button" onclick="analyzeSelected()">批量分析</button>
    <button class="action-quiet" id="compare-selected-btn" type="button" onclick="openCompareSelected()">对比</button>
    <div class="batch-divider"></div>
    <button class="action-quiet" type="button" onclick="batchSetState('favorites');">关注</button>
    <button class="action-quiet" type="button" onclick="batchSetState('watch_later');">待看</button>
    <button class="action-quiet" type="button" onclick="batchSetState('read');">已读</button>
    <button class="action-quiet" type="button" onclick="batchSetState('ignored');">忽略</button>
    <div class="menu-wrap" data-menu-id="batch-more-menu">
      <button class="action-quiet menu-toggle" type="button" aria-haspopup="menu" aria-expanded="false" onclick="toggleMenu(event,'batch-more-menu')">更多<span class="menu-caret"></span></button>
      <div class="menu-panel upward align-left" id="batch-more-menu-panel">
        <button class="menu-item" type="button" onclick="selectVisible();closeMenus();">重新全选本页</button>
        <button class="menu-item" type="button" onclick="clearSelected();closeMenus();">清空选择</button>
      </div>
    </div>
  </div>
</div>

<div class="toast" id="toast" role="status" aria-live="polite" aria-atomic="true"></div>
<input id="import-user-state-input" type="file" accept=".json,application/json" hidden>

<section class="overlay settings" id="settings-modal">
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="panel-title">设置</div>
        <div class="sub">配置 GitHub Token、代理、刷新频率与条目上限。主窗口关闭会直接退出程序。</div>
      </div>
      <button class="action-quiet" type="button" onclick="closeSettings()">关闭</button>
    </div>
    <div class="panel-body settings-grid">
      <div class="settings-form">
        <label class="field">
          <span class="field-label">GitHub Token</span>
          <input id="setting-token" class="field-input" type="password" placeholder="可选，用于提高请求稳定性">
          <span class="field-meta" id="setting-token-presence">未配置 GitHub Token。</span>
          <span class="field-meta" id="setting-token-status" data-state="idle">会自动校验当前 Token，可区分空值、无效、权限不足和可正常使用四种状态。</span>
          <label class="checkline">
            <input id="setting-clear-token" type="checkbox">
            <span>保存时清空当前 Token</span>
          </label>
        </label>
        <label class="field">
          <span class="field-label">代理地址</span>
          <input id="setting-proxy" class="field-input" type="text" placeholder="留空则自动探测">
          <span class="field-meta" id="setting-proxy-presence">未配置代理，留空时会继续自动探测。</span>
          <label class="checkline">
            <input id="setting-clear-proxy" type="checkbox">
            <span>保存时清空当前代理</span>
          </label>
        </label>
        <div class="settings-inline">
          <label class="field">
            <span class="field-label">刷新间隔</span>
            <input id="setting-refresh-hours" class="field-input" type="number" min="1" max="24" placeholder="1">
            <span class="field-meta">1 - 24 小时</span>
          </label>
          <label class="field">
            <span class="field-label">结果上限</span>
            <input id="setting-result-limit" class="field-input" type="number" min="10" max="100" placeholder="25">
            <span class="field-meta">10 - 100 条</span>
          </label>
          <label class="field">
            <span class="field-label">端口</span>
            <input id="setting-port" class="field-input" type="number" min="1" max="65535" placeholder="8080">
            <span class="field-meta">修改后重启生效</span>
          </label>
        </div>
        <div class="switch-row">
          <div class="switch-copy">
            <div class="switch-title">开机启动</div>
            <div class="switch-desc">随系统自动启动，方便后台持续跟踪 GitHub 变化。</div>
          </div>
          <label class="switch">
            <input id="setting-auto-start" type="checkbox">
            <span class="switch-track">
              <span class="switch-thumb"></span>
            </span>
          </label>
        </div>
      </div>
      <div class="notice">网络提醒：程序本身不提供 VPN。如果趋势列表刷不出来、仓库详情加载失败，通常需要先开启代理或 VPN，然后把代理地址填到上面的“代理地址”里。</div>
      <div class="notice">关闭提醒：主窗口关闭会直接退出程序；如需明确结束当前会话，也可以使用下方“退出程序”。</div>
      <div class="sub" id="settings-runtime-hint"></div>
      <div class="settings-actions">
        <button class="action-primary" type="button" onclick="saveSettings()">保存设置</button>
        <button class="action-quiet danger" type="button" onclick="exitApp()">退出程序</button>
      </div>
    </div>
  </div>
</section>

<section class="overlay detail" id="detail-modal">
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="panel-title">仓库详情</div>
        <div class="sub" id="detail-title">加载中...</div>
      </div>
      <button class="action-quiet" type="button" onclick="closeDetail()">关闭</button>
    </div>
    <div class="panel-body" id="detail-body"></div>
  </div>
</section>

<section class="overlay compare" id="compare-modal">
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="panel-title">仓库对比</div>
        <div class="sub">把两个仓库按同一组维度并排展开，便于快速判断方向、热度和长期价值。</div>
      </div>
      <button class="action-quiet" type="button" onclick="closeCompare()">关闭</button>
    </div>
    <div class="panel-body" id="compare-body"></div>
  </div>
</section>

<script>
"""

HTML_TAIL = """</script>
</body>
</html>
"""

HTML_TEMPLATE = HTML_HEAD + CSS + HTML_BODY + JS + HTML_TAIL


def build_html(
    *,
    app_name: str,
    snapshot: dict[str, object],
    user_state: dict[str, object],
    discovery_state: dict[str, object],
    settings: dict[str, object],
    periods: list[dict[str, object]],
    states: list[dict[str, object]],
    note: str,
    pending: bool,
    control_token: str = "",
) -> str:
    payload = json.dumps(
        {
            "snapshot": snapshot,
            "userState": user_state,
            "discoveryState": discovery_state,
            "settings": settings,
            "periods": periods,
            "states": states,
            "note": note,
            "pending": pending,
            "controlToken": control_token,
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")
    return HTML_TEMPLATE.replace("__APP_NAME__", app_name).replace("__PAYLOAD__", payload)
