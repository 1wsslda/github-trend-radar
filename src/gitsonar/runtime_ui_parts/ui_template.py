#!/usr/bin/env python3
from __future__ import annotations

import json

from .ui_css import CSS
from .ui_js import JS

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
  <header class="masthead">
    <div class="masthead-copy">
      <span class="hero-kicker">GitHub Intelligence Desk</span>
      <div class="masthead-title-row">
        <h1 class="masthead-title">__APP_NAME__</h1>
        <span class="masthead-badge">Reading-first Workspace</span>
      </div>
      <p class="masthead-sub">把 GitHub 趋势、收藏追踪、仓库详情和 ChatGPT 分析收拢成一个更适合长期阅读的桌面情报台。</p>
    </div>
    <div class="masthead-side">
      <div class="status-card">
        <span class="status-label">Runtime</span>
        <div class="runtime-note" id="note"></div>
      </div>
      <div class="nav-actions">
      <button class="action-quiet" type="button" onclick="refreshNow()">刷新</button>
      <button class="action-quiet" type="button" onclick="hideToTray()">隐藏</button>
      <button class="action-quiet" type="button" onclick="openSettings()">设置</button>
      <div class="menu-wrap" data-menu-id="app-more-menu">
        <button class="action-quiet menu-toggle" type="button" aria-haspopup="menu" aria-expanded="false" onclick="toggleMenu(event,'app-more-menu')">更多<span class="menu-caret"></span></button>
        <div class="menu-panel" id="app-more-menu-panel">
          <button class="menu-item" type="button" onclick="exportUserState();closeMenus();">导出数据</button>
          <button class="menu-item" type="button" onclick="beginImportUserState('merge');closeMenus();">导入并合并</button>
          <button class="menu-item" type="button" onclick="beginImportUserState('replace');closeMenus();">导入并覆盖</button>
          <button class="menu-item" type="button" onclick="syncGitHubStars();closeMenus();">从 GitHub 同步星标</button>
          <button class="menu-item" type="button" id="clear-updates-menu-item" onclick="clearFavoriteUpdates();closeMenus();" hidden>清空关注更新</button>
        </div>
      </div>
      </div>
    </div>
  </header>

  <section class="toolbar">
    <div class="control-shell">
      <div class="toolbar-head">
        <div class="toolbar-copy">
          <div class="summary">当前面板可见 <span class="metric-number" id="visible-count">0</span><span id="visible-label"> 个仓库</span> · 已选 <span class="metric-number" id="selected-count">0</span> 项</div>
          <div class="sub" style="line-height:1.8;">程序本身不提供 VPN；如果当前网络无法访问 GitHub，请先准备好代理或 VPN，再到“设置”里填写代理地址。<br><span style="color:var(--accent);opacity:0.85;">⌨️ <strong style="font-weight:600">快捷操作</strong>：按 <strong>↑ / ↓</strong> 游走卡片 · <strong>Space</strong> 勾选当前仓库 · <strong>Shift + 1~4</strong> 一键批量分发收纳。</span></div>
        </div>
      </div>

      <div class="toolbar-main">
        <label class="field search-field">
          <span class="field-label">搜索</span>
          <span class="field-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="7"></circle>
              <line x1="20" y1="20" x2="16.65" y2="16.65"></line>
            </svg>
          </span>
          <input id="search" class="field-input" type="search" placeholder="搜索仓库 / 描述 / 语言 / 更新内容">
        </label>

        <div class="action-split menu-wrap" data-menu-id="ai-target-menu">
          <button class="action-primary split-main" id="analyze-visible-btn" type="button" onclick="analyzeVisible()">
            <span class="split-main-label">
              <span class="split-main-title">分析当前列表</span>
              <span class="split-main-note" id="ai-target-label">ChatGPT 网页版</span>
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
      </div>

      <div class="toolbar-filters">
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
      </div>

      <section class="discover-shell" id="discover-shell" hidden>
        <div class="discover-grid">
          <label class="field">
            <span class="field-label">发现关键词</span>
            <input id="discover-query" class="field-input" type="search" placeholder="例如 agent / AI agent framework / 图数据库">
          </label>

          <label class="field">
            <span class="field-label">语言限定</span>
            <input id="discover-language" class="field-input" type="text" placeholder="可选，如 Python / TypeScript">
          </label>

          <label class="field">
            <span class="field-label">结果数</span>
            <input id="discover-limit" class="field-input" type="number" min="5" max="50" step="1">
          </label>

          <div class="field select-field custom-select" data-custom-select-for="discover-ranking-profile" data-menu-id="discover-ranking-profile-menu">
            <span class="field-label">排序模式</span>
            <select id="discover-ranking-profile" class="field-input native-select" aria-hidden="true" tabindex="-1">
              <option value="balanced">综合平衡</option>
              <option value="hot">偏热门</option>
              <option value="fresh">偏新项目</option>
              <option value="builder">偏工程可用</option>
              <option value="trend">偏趋势</option>
            </select>
            <button class="field-input select-trigger" id="discover-ranking-profile-trigger" type="button" aria-haspopup="listbox" aria-expanded="false" aria-controls="discover-ranking-profile-menu-panel" onclick="toggleMenu(event,'discover-ranking-profile-menu')">
              <span class="select-trigger-text">综合平衡</span>
            </button>
            <div class="menu-panel select-menu" id="discover-ranking-profile-menu-panel" role="listbox" aria-labelledby="discover-ranking-profile-trigger"></div>
          </div>
        </div>

        <div class="discover-actions">
          <label class="checkline"><input id="discover-auto-expand" type="checkbox"> <span>自动扩展相关词</span></label>
          <label class="checkline"><input id="discover-save-query" type="checkbox"> <span>保存这次搜索</span></label>
          <button class="action-primary" id="discover-run-btn" type="button" onclick="runDiscovery()">开始发现</button>
          <button class="action-quiet danger" id="discover-cancel-btn" type="button" onclick="cancelDiscovery()" hidden>取消</button>
          <button class="action-quiet" id="discover-clear-btn" type="button" onclick="clearDiscovery()">清空结果</button>
        </div>

        <div class="discover-panel">
          <div class="group-label">已保存搜索</div>
          <div class="discover-saved" id="discover-saved"></div>
        </div>

        <div class="discover-meta" id="discover-meta"></div>
        <div class="discover-top" id="discover-top"></div>
      </section>
    </div>
  </section>

  <div class="tabs" id="tabs"></div>
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
        <div class="sub">配置 GitHub Token、代理、刷新频率、条目上限和关闭行为。</div>
      </div>
      <button class="action-quiet" type="button" onclick="closeSettings()">关闭</button>
    </div>
    <div class="panel-body settings-grid">
      <div class="settings-form">
        <label class="field">
          <span class="field-label">GitHub Token</span>
          <input id="setting-token" class="field-input" type="password" placeholder="可选，用于提高请求稳定性">
        </label>
        <label class="field">
          <span class="field-label">代理地址</span>
          <input id="setting-proxy" class="field-input" type="text" placeholder="留空则自动探测">
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

        <div class="field select-field custom-select" data-custom-select-for="setting-close-behavior" data-menu-id="setting-close-behavior-menu">
          <span class="field-label">关闭行为</span>
          <select id="setting-close-behavior" class="field-input native-select" aria-hidden="true" tabindex="-1">
            <option value="tray">关闭主窗口时保留托盘运行</option>
            <option value="exit">关闭主窗口时直接退出程序</option>
          </select>
          <button class="field-input select-trigger" id="setting-close-behavior-trigger" type="button" aria-haspopup="listbox" aria-expanded="false" aria-controls="setting-close-behavior-menu-panel" onclick="toggleMenu(event,'setting-close-behavior-menu')">
            <span class="select-trigger-text">关闭主窗口时保留托盘运行</span>
          </button>
          <div class="menu-panel select-menu upward" id="setting-close-behavior-menu-panel" role="listbox" aria-labelledby="setting-close-behavior-trigger"></div>
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
      <div class="notice">关闭提醒：如果选择“保留托盘运行”，主窗口关闭后程序仍会继续运行，图标可能收在任务栏右下角的隐藏图标里。</div>
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
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")
    return HTML_TEMPLATE.replace("__APP_NAME__", app_name).replace("__PAYLOAD__", payload)
