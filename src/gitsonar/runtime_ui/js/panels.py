#!/usr/bin/env python3
from __future__ import annotations

JS = r"""function compareByKey(a, b, key){
  if(key === "trending") return (a.rank || 9999) - (b.rank || 9999) || (b.gained || 0) - (a.gained || 0) || (b.stars || 0) - (a.stars || 0);
  if(key === "gained") return (b.gained || 0) - (a.gained || 0) || (b.stars || 0) - (a.stars || 0) || (a.rank || 9999) - (b.rank || 9999);
  if(key === "forks") return (b.forks || 0) - (a.forks || 0) || (b.stars || 0) - (a.stars || 0) || (a.rank || 9999) - (b.rank || 9999);
  if(key === "name") return String(a.full_name || "").localeCompare(String(b.full_name || ""), "zh-Hans-CN") || (a.rank || 9999) - (b.rank || 9999);
  if(key === "language") return String(a.language || "").localeCompare(String(b.language || ""), "zh-Hans-CN") || (b.stars || 0) - (a.stars || 0) || (a.rank || 9999) - (b.rank || 9999);
  return (b.stars || 0) - (a.stars || 0) || (b.gained || 0) - (a.gained || 0) || (a.rank || 9999) - (b.rank || 9999);
}

function visibleRepos(){
  if(panel === UPDATE_PANEL_KEY) return [];
  const raw = panelRepoSource();
  const searchNode = document.getElementById("search");
  const languageNode = document.getElementById("language");
  const query = (searchNode?.value || "").trim().toLowerCase();
  const language = panel === DISCOVER_PANEL_KEY ? "" : (languageNode?.value || "");
  const repos = raw.filter(repo => {
    const haystack = `${repo.full_name} ${repo.description || ""} ${repo.description_raw || ""} ${repo.language || ""} ${repo.source_label || ""}`.toLowerCase();
    if(query && !haystack.includes(query)) return false;
    if(language && (repo.language || "") !== language) return false;
    if(panel === DISCOVER_PANEL_KEY) return true;
    if(stateFilter === "unmarked"){
      if(stateDefs().some(state => (userState[state.key] || []).includes(repo.url))) return false;
    }else if(stateFilter && !((userState[stateFilter] || []).includes(repo.url))){
      return false;
    }
    return true;
  });
  if(panel === DISCOVER_PANEL_KEY){
    repos.sort((a, b) => (b.composite_score || 0) - (a.composite_score || 0) || (b.relevance_score || 0) - (a.relevance_score || 0) || (b.hot_score || 0) - (a.hot_score || 0) || (b.stars || 0) - (a.stars || 0) || (a.rank || 9999) - (b.rank || 9999));
    return repos;
  }
  const sortKeys = [sortPrimary, "trending"].filter((key, index, array) => key && array.indexOf(key) === index);
  repos.sort((a, b) => {
    for(const key of sortKeys){
      const result = compareByKey(a, b, key);
      if(result) return result;
    }
    return 0;
  });
  return repos;
}

function visibleUpdates(){
  if(panel !== UPDATE_PANEL_KEY) return [];
  const searchNode = document.getElementById("search");
  const query = (searchNode?.value || "").trim().toLowerCase();
  return (userState.favorite_updates || []).filter(update => {
    const haystack = `${update.full_name || ""} ${(update.changes || []).join(" ")} ${update.latest_release_tag || ""}`.toLowerCase();
    return !query || haystack.includes(query);
  });
}

function visibleLinkList(){
  return panel === UPDATE_PANEL_KEY ? visibleUpdates().map(update => update.url) : visibleRepos().map(repo => repo.url);
}

function tabsData(){
  return [
    ...periodDefs().map(period => ({
      key:period.key,
      label:period.label,
      count:current(period.key).length,
      family:"trend",
    })),
    {key:DISCOVER_PANEL_KEY, label:"发现", count:discoveryResults().length, family:"discover"},
    ...stateDefs().map(state => ({
      key:`saved:${state.key}`,
      label:state.label,
      count:(userState[state.key] || []).length,
      family:"library",
    })),
    {key:UPDATE_PANEL_KEY, label:"更新", count:(userState.favorite_updates || []).length, family:"updates"},
  ];
}

function ensureValidPanel(){
  panel = normalizePanelKey(panel);
  const keys = new Set(tabsData().map(tab => tab.key));
  if(!keys.has(panel)){
    panel = "daily";
    localStorage.setItem("gtr-tab", panel);
  }
}

function panelMeta(key = panel){
  return tabsData().find(tab => tab.key === key) || null;
}

function panelFamily(key = panel){
  return panelMeta(key)?.family || "trend";
}

function renderTabs(){
  const tabs = tabsData();
  const activeFamily = panelFamily();
  const trendTabs = tabs.filter(tab => tab.family === "trend");
  const libraryTabs = tabs.filter(tab => tab.family === "library");
  const discoverTab = tabs.find(tab => tab.family === "discover");
  const updatesTab = tabs.find(tab => tab.family === "updates");
  const activeTrend = trendTabs.find(tab => tab.key === panel) || trendTabs[0];
  const activeLibrary = libraryTabs.find(tab => tab.key === panel) || libraryTabs[0];
  const libraryCount = libraryTabs.reduce((sum, tab) => sum + (tab.count || 0), 0);
  const trendMenu = trendTabs.map(tab => `
    <button class="menu-item ${tab.key === panel ? "active" : ""}" type="button" onclick='setPanel(${JSON.stringify(tab.key)});closeMenus();'>
      <span>${h(tab.label)}</span>
      <span class="nav-count">${tab.count}</span>
    </button>
  `).join("");
  const libraryMenu = libraryTabs.map(tab => `
    <button class="menu-item ${tab.key === panel ? "active" : ""}" type="button" onclick='setPanel(${JSON.stringify(tab.key)});closeMenus();'>
      <span>${h(tab.label)}</span>
      <span class="nav-count">${tab.count}</span>
    </button>
  `).join("");

  document.getElementById("tabs").innerHTML = `<div class="nav-main">
    <div class="menu-wrap" data-menu-id="nav-trend-menu">
      <button class="nav-pill menu-toggle ${activeFamily === "trend" ? "active" : ""}" type="button" aria-haspopup="menu" aria-expanded="false" onclick='toggleMenu(event, "nav-trend-menu")'>
        趋势
        ${activeTrend ? `<span class="nav-pill-note">${h(activeTrend.label)}</span><span class="nav-count">${activeTrend.count}</span>` : ""}
        <span class="menu-caret"></span>
      </button>
      <div class="menu-panel align-left nav-menu-panel" id="nav-trend-menu-panel">
        ${trendMenu}
      </div>
    </div>
    <button class="nav-pill ${panel === DISCOVER_PANEL_KEY ? "active" : ""}" type="button" onclick='setPanel(${JSON.stringify(DISCOVER_PANEL_KEY)})'>
      发现
      ${discoverTab ? `<span class="nav-count">${discoverTab.count}</span>` : ""}
    </button>
    <div class="menu-wrap" data-menu-id="nav-library-menu">
      <button class="nav-pill menu-toggle ${activeFamily === "library" ? "active" : ""}" type="button" aria-haspopup="menu" aria-expanded="false" onclick='toggleMenu(event, "nav-library-menu")'>
        我的库
        ${activeLibrary ? `<span class="nav-pill-note">${h(activeLibrary.label)}</span>` : ""}
        <span class="nav-count">${libraryCount}</span>
        <span class="menu-caret"></span>
      </button>
      <div class="menu-panel align-left nav-menu-panel" id="nav-library-menu-panel">
        ${libraryMenu}
      </div>
    </div>
    <button class="nav-pill ${panel === UPDATE_PANEL_KEY ? "active" : ""}" type="button" onclick='setPanel(${JSON.stringify(UPDATE_PANEL_KEY)})'>
      更新
      ${updatesTab ? `<span class="nav-count">${updatesTab.count}</span>` : ""}
    </button>
  </div>`;
}

function currentStateFilterLabel(){
  if(stateFilter === "unmarked") return "未标记";
  return stateDefs().find(state => state.key === stateFilter)?.label || "全部";
}

function currentSortLabel(){
  return SORT_LABELS[sortPrimary] || "总星标";
}

function panelSummaryText(key = panel){
  const meta = panelMeta(key);
  if(!meta) return "今日趋势 · 0 个仓库";
  if(key === DISCOVER_PANEL_KEY) return `${meta.label} · ${meta.count || 0} 个候选`;
  if(key === UPDATE_PANEL_KEY) return `${meta.label} · ${meta.count || 0} 条更新`;
  return `${meta.label} · ${meta.count || 0} 个仓库`;
}

function renderWorkspaceSummaryStrip(){
  const strip = document.getElementById("workspace-summary-strip");
  if(!strip) return;

  if(panel === DISCOVER_PANEL_KEY){
    const results = discoveryResults();
    const query = String(activeDiscoveryJob?.query?.query || discoveryState.last_query?.query || discoverDraft.query || "").trim();
    if(!query && !results.length && !activeDiscoveryJob){
      strip.hidden = true;
      strip.innerHTML = "";
      return;
    }
    const ranking = discoveryRankingLabel(activeDiscoveryJob?.query?.ranking_profile || discoveryState.last_query?.ranking_profile || discoverDraft.rankingProfile);
    const status = discoveryBusy ? (activeDiscoveryJob?.stage_label || "发现中") : (results.length ? "结果已就绪" : "等待运行");
    strip.hidden = false;
    strip.innerHTML = `
      <div class="summary-strip-row">
        <span class="summary-strip-label">发现摘要</span>
        ${query ? `<span class="summary-strip-item">关键词 <strong>${h(query)}</strong></span>` : ""}
        <span class="summary-strip-item">结果 <strong>${results.length}</strong></span>
        <span class="summary-strip-item">排序 <strong>${h(ranking)}</strong></span>
        <span class="summary-strip-item">状态 <strong>${h(status)}</strong></span>
      </div>
    `;
    return;
  }

  const searchValue = String(document.getElementById("search")?.value || "").trim();
  const tokens = [];
  if(searchValue) tokens.push(`搜索 <strong>${h(searchValue)}</strong>`);
  if(languageFilter) tokens.push(`语言 <strong>${h(languageFilter)}</strong>`);
  if(stateFilter) tokens.push(`状态 <strong>${h(currentStateFilterLabel())}</strong>`);
  if(sortPrimary !== "stars") tokens.push(`排序 <strong>${h(currentSortLabel())}</strong>`);
  if(!tokens.length){
    strip.hidden = true;
    strip.innerHTML = "";
    return;
  }
  strip.hidden = false;
  strip.innerHTML = `
    <div class="summary-strip-row">
      <span class="summary-strip-label">当前阅读视图</span>
      ${tokens.map(token => `<span class="summary-strip-item">${token}</span>`).join("")}
    </div>
  `;
}

function renderDiscoverEmptyState(){
  const results = discoveryResults();
  const lastQuery = discoveryState.last_query || {};
  const currentQuery = String(discoverDraft.query || "").trim();
  const primaryAction = currentQuery ? "runDiscovery()" : "toggleControlDrawer(true)";
  const primaryLabel = currentQuery ? "开始发现" : "打开发现参数";

  if(discoveryBusy && !results.length){
    return `<div class="workspace-empty-card">
      <div class="workspace-empty-kicker">Discovery In Progress</div>
      <div class="workspace-empty-title">${h(activeDiscoveryJob?.stage_label || "正在准备发现结果")}</div>
      <div class="workspace-empty-copy">${h(activeDiscoveryJob?.message || "GitSonar 正在执行首轮检索、补全详情和综合重排。")}</div>
      <div class="workspace-empty-actions">
        <button class="action-primary" type="button" onclick="toggleControlDrawer(true)">查看发现参数</button>
        <button class="action-quiet danger" type="button" onclick="cancelDiscovery()">取消任务</button>
      </div>
    </div>`;
  }

  if(results.length) return "";

  if(lastQuery.query){
    return `<div class="workspace-empty-card">
      <div class="workspace-empty-kicker">Recent Discovery</div>
      <div class="workspace-empty-title">从上一次发现继续</div>
      <div class="workspace-empty-copy">最近一次关键词是 <strong>${h(lastQuery.query)}</strong>，共拿到 <strong>${discoveryResults().length}</strong> 个候选${discoveryState.last_run_at ? `，运行于 ${h(discoveryState.last_run_at)}` : ""}。</div>
      <div class="workspace-empty-actions">
        <button class="action-primary" type="button" onclick="${primaryAction}">${primaryLabel}</button>
        <button class="action-quiet" type="button" onclick="toggleControlDrawer(true)">调整参数</button>
      </div>
    </div>`;
  }

  return `<div class="workspace-empty-card">
    <div class="workspace-empty-kicker">Start Discovery</div>
    <div class="workspace-empty-title">先给一个关键词，再让结果占据主画布</div>
    <div class="workspace-empty-copy">发现页默认保持轻量。输入关键词、语言限定和排序偏好后，运行结果会直接进入主区域，只保留一条摘要带提示当前状态。</div>
    <div class="workspace-empty-actions">
      <button class="action-primary" type="button" onclick="${primaryAction}">${primaryLabel}</button>
      <button class="action-quiet" type="button" onclick="toggleControlDrawer(true)">查看最近搜索</button>
    </div>
  </div>`;
}

function syncWorkspaceHeader(){
  const summaryNode = document.getElementById("panel-summary");
  if(summaryNode) summaryNode.textContent = panelSummaryText();
}

function syncWorkspaceCanvas(){
  const introNode = document.getElementById("canvas-intro");
  const cardsNode = document.getElementById("cards");
  if(!introNode || !cardsNode) return;
  if(panel !== DISCOVER_PANEL_KEY){
    introNode.hidden = true;
    introNode.innerHTML = "";
    cardsNode.classList.remove("cards--discover-empty");
    renderWorkspaceSummaryStrip();
    return;
  }
  const emptyMarkup = renderDiscoverEmptyState();
  introNode.hidden = !emptyMarkup;
  introNode.innerHTML = emptyMarkup;
  cardsNode.classList.toggle("cards--discover-empty", !!emptyMarkup);
  renderWorkspaceSummaryStrip();
}

function syncControlDrawer(){
  const isDiscoverPanel = panel === DISCOVER_PANEL_KEY;
  const isUpdatePanel = panel === UPDATE_PANEL_KEY;
  const trigger = document.getElementById("control-drawer-trigger");
  const triggerLabel = document.getElementById("control-drawer-label");
  const drawerTitle = document.getElementById("control-drawer-title");
  const drawerSubtitle = document.getElementById("control-drawer-subtitle");
  const listSection = document.getElementById("control-drawer-list");
  const discoverSection = document.getElementById("control-drawer-discover");
  const updatesSection = document.getElementById("control-drawer-updates");

  if(triggerLabel) triggerLabel.textContent = isDiscoverPanel ? "发现参数" : "筛选";
  if(trigger){
    trigger.classList.toggle("active", isControlDrawerVisible());
    trigger.setAttribute("aria-expanded", isControlDrawerVisible() ? "true" : "false");
  }

  if(drawerTitle){
    drawerTitle.textContent = isDiscoverPanel ? "发现参数" : (isUpdatePanel ? "筛选" : "筛选");
  }
  if(drawerSubtitle){
    drawerSubtitle.textContent = isDiscoverPanel
      ? "发现页把表单折叠进控制层，只在主区域保留摘要和结果列表。"
      : (isUpdatePanel
        ? "更新页保持轻量阅读模式，主画布优先展示仓库变化。"
        : "趋势列表和我的库把状态、语言、排序收进抽屉，首屏先看卡片。");
  }

  if(listSection) listSection.hidden = isDiscoverPanel || isUpdatePanel;
  if(discoverSection) discoverSection.hidden = !isDiscoverPanel;
  if(updatesSection) updatesSection.hidden = !isUpdatePanel;
}

function syncControlStates(){
  const isUpdatePanel = panel === UPDATE_PANEL_KEY;
  const isDiscoverPanel = panel === DISCOVER_PANEL_KEY;
  const disableListControls = isUpdatePanel || isDiscoverPanel;
  document.getElementById("language").disabled = disableListControls;
  document.querySelectorAll("#state-filter-seg .seg-btn").forEach(btn => { btn.disabled = disableListControls; });
  document.querySelectorAll("#sort-primary-seg .seg-btn").forEach(btn => { btn.disabled = disableListControls; });
  document.getElementById("analyze-visible-btn").disabled = isUpdatePanel;
  document.getElementById("ai-target-trigger").disabled = isUpdatePanel;
  const stateFilterGroup = document.getElementById("state-filter-group");
  stateFilterGroup.classList.toggle("is-disabled", disableListControls);
  document.getElementById("sort-primary-group").classList.toggle("is-disabled", disableListControls);
  document.getElementById("clear-updates-menu-item").hidden = !isUpdatePanel || !(userState.favorite_updates || []).length;
  syncCustomSelect("language");
  syncControlDrawer();
}"""
