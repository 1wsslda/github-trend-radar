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
  const query = panel === DISCOVER_PANEL_KEY ? "" : (searchNode?.value || "").trim().toLowerCase();
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
  rememberPanelPreference(panel);
}

function panelMeta(key = panel){
  return tabsData().find(tab => tab.key === key) || null;
}

function panelFamily(key = panel){
  return panelMeta(key)?.family || "trend";
}

function rememberPanelPreference(key = panel){
  const normalized = normalizePanelKey(key);
  const family = panelFamily(normalized);
  if(family === "trend") localStorage.setItem("gtr-tab-trend", normalized);
  if(family === "library") localStorage.setItem("gtr-tab-library", normalized);
}

function preferredFamilyPanel(family){
  if(family === "trend"){
    const stored = normalizePanelKey(localStorage.getItem("gtr-tab-trend") || "");
    if(panelFamily(stored) === "trend") return stored;
    return periodDefs()[0]?.key || "daily";
  }
  if(family === "library"){
    const stored = normalizePanelKey(localStorage.getItem("gtr-tab-library") || "");
    if(panelFamily(stored) === "library") return stored;
    const fallback = stateDefs()[0]?.key || "favorites";
    return `saved:${fallback}`;
  }
  return family === "discover" ? DISCOVER_PANEL_KEY : UPDATE_PANEL_KEY;
}

function setPrimaryPanel(family){
  if(family === "trend" || family === "library"){
    setPanel(preferredFamilyPanel(family));
    return;
  }
  setPanel(family === "discover" ? DISCOVER_PANEL_KEY : UPDATE_PANEL_KEY);
}

let workspaceNavOffsetFrame = 0;
let workspaceNavOffsetObserver = null;

function applyWorkspaceNavOffset(){
  const page = document.querySelector(".page");
  const navShell = document.querySelector(".workspace-nav-shell");
  const navSection = document.querySelector(".workspace-nav");
  if(!page || !navShell || !navSection) return;

  const navTop = parseFloat(getComputedStyle(navShell).top || "0") || 0;
  const navGap = parseFloat(getComputedStyle(navSection).marginBottom || "0") || 0;
  const navHeight = navShell.getBoundingClientRect().height || navShell.offsetHeight || 0;
  page.style.setProperty("--workspace-nav-offset", `${Math.ceil(navTop + navHeight + navGap)}px`);
}

function syncWorkspaceNavOffset(){
  if(workspaceNavOffsetFrame) cancelAnimationFrame(workspaceNavOffsetFrame);
  workspaceNavOffsetFrame = requestAnimationFrame(() => {
    workspaceNavOffsetFrame = 0;
    applyWorkspaceNavOffset();
  });
}

function observeWorkspaceNavOffset(){
  if(workspaceNavOffsetObserver || typeof ResizeObserver !== "function") return;
  const navShell = document.querySelector(".workspace-nav-shell");
  const tabsRoot = document.getElementById("tabs");
  if(!navShell) return;

  workspaceNavOffsetObserver = new ResizeObserver(() => {
    syncWorkspaceNavOffset();
  });
  workspaceNavOffsetObserver.observe(navShell);
  if(tabsRoot) workspaceNavOffsetObserver.observe(tabsRoot);
}

function renderPrimaryNav(activeFamily, activeTrend, discoverTab, libraryCount, updatesTab){
  const tabsRoot = document.getElementById("tabs");
  if(!tabsRoot) return;

  tabsRoot.innerHTML = `<nav class="workspace-primary-nav" aria-label="\u5de5\u4f5c\u533a\u89c6\u56fe\u5207\u6362">
    <button class="workspace-primary-link ${activeFamily === "trend" ? "active" : ""}" type="button" onclick='setPrimaryPanel("trend")'>
      <span class="workspace-primary-label">\u8d8b\u52bf</span>
      ${activeTrend ? `<span class="workspace-primary-count">${activeTrend.count}</span>` : ""}
    </button>
    <button class="workspace-primary-link ${activeFamily === "discover" ? "active" : ""}" type="button" onclick='setPrimaryPanel("discover")'>
      <span class="workspace-primary-label">\u53d1\u73b0</span>
      ${discoverTab ? `<span class="workspace-primary-count">${discoverTab.count}</span>` : ""}
    </button>
    <button class="workspace-primary-link ${activeFamily === "library" ? "active" : ""}" type="button" onclick='setPrimaryPanel("library")'>
      <span class="workspace-primary-label">\u6211\u7684\u5e93</span>
      <span class="workspace-primary-count">${libraryCount}</span>
    </button>
    <button class="workspace-primary-link ${activeFamily === "updates" ? "active" : ""}" type="button" onclick='setPrimaryPanel("updates")'>
      <span class="workspace-primary-label">\u66f4\u65b0</span>
      ${updatesTab ? `<span class="workspace-primary-count">${updatesTab.count}</span>` : ""}
    </button>
  </nav>`;
}

function renderWorkspaceSubnav(activeFamily, trendTabs, libraryTabs, activeTrendKey, activeLibraryKey){
  const subnav = document.getElementById("workspace-subnav");
  if(!subnav) return;

  if(activeFamily === "trend"){
    subnav.hidden = false;
    subnav.innerHTML = `<div class="workspace-subnav-row" aria-label="\u8d8b\u52bf\u65f6\u95f4\u8303\u56f4">
      ${trendTabs.map(tab => `
        <button class="workspace-subnav-link ${tab.key === activeTrendKey ? "active" : ""}" type="button" onclick='setPanel(${JSON.stringify(tab.key)})'>
          <span class="workspace-subnav-label">${h(tab.label)}</span>
          <span class="workspace-subnav-count">${tab.count}</span>
        </button>
      `).join("")}
    </div>`;
    return;
  }

  if(activeFamily === "library"){
    subnav.hidden = false;
    subnav.innerHTML = `<div class="workspace-subnav-row" aria-label="\u6211\u7684\u5e93\u72b6\u6001">
      ${libraryTabs.map(tab => `
        <button class="workspace-subnav-link ${tab.key === activeLibraryKey ? "active" : ""}" type="button" onclick='setPanel(${JSON.stringify(tab.key)})'>
          <span class="workspace-subnav-label">${h(tab.label)}</span>
          <span class="workspace-subnav-count">${tab.count}</span>
        </button>
      `).join("")}
    </div>`;
    return;
  }

  subnav.hidden = true;
  subnav.innerHTML = "";
}
function renderTabs(){
  const tabs = tabsData();
  const activeFamily = panelFamily();
  const trendTabs = tabs.filter(tab => tab.family === "trend");
  const libraryTabs = tabs.filter(tab => tab.family === "library");
  const discoverTab = tabs.find(tab => tab.family === "discover");
  const updatesTab = tabs.find(tab => tab.family === "updates");
  const activeTrendKey = activeFamily === "trend" ? panel : preferredFamilyPanel("trend");
  const activeLibraryKey = activeFamily === "library" ? panel : preferredFamilyPanel("library");
  const activeTrend = trendTabs.find(tab => tab.key === activeTrendKey) || trendTabs[0];
  const activeLibrary = libraryTabs.find(tab => tab.key === activeLibraryKey) || libraryTabs[0];
  const libraryCount = libraryTabs.reduce((sum, tab) => sum + (tab.count || 0), 0);

  renderPrimaryNav(activeFamily, activeTrend, discoverTab, libraryCount, updatesTab);
  renderWorkspaceSubnav(activeFamily, trendTabs, libraryTabs, activeTrend?.key || "", activeLibrary?.key || "");
  observeWorkspaceNavOffset();
  syncWorkspaceNavOffset();
}

function currentStateFilterLabel(){
  if(stateFilter === "unmarked") return "未标记";
  return stateDefs().find(state => state.key === stateFilter)?.label || "全部";
}

function currentSortLabel(){
  return SORT_LABELS[sortPrimary] || "总星标";
}

function renderWorkspaceSummaryStrip(){
  const strip = document.getElementById("workspace-summary-strip");
  if(!strip) return;

  if(panel === DISCOVER_PANEL_KEY){
    const query = currentDiscoveryQueryText();
    if(!query && !discoveryResults().length && !activeDiscoveryJob){
      strip.hidden = true;
      strip.innerHTML = "";
      return;
    }
    const ranking = discoveryRankingLabel(currentDiscoveryQuery().ranking_profile || discoverDraft.rankingProfile);
    const status = currentDiscoveryStatusLabel();
    strip.hidden = false;
    strip.innerHTML = `
      <div class="summary-strip-row">
        <span class="summary-strip-label">当前搜索</span>
        ${query ? `<span class="summary-strip-item">关键词 <strong>${h(query)}</strong></span>` : ""}
        <span class="summary-strip-item">当前排序 <strong>${h(ranking)}</strong></span>
        <span class="summary-strip-item">结果上限 <strong>${currentDiscoveryLimit()}</strong></span>
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

function syncWorkspaceBarModes(){
  const isDiscoverPanel = panel === DISCOVER_PANEL_KEY;
  const isUpdatePanel = panel === UPDATE_PANEL_KEY;
  const filterGroup = document.querySelector(".workspace-filter-group");
  const actionGroup = document.querySelector(".workspace-action-group");
  const searchWrap = document.querySelector(".workspace-search-wrap");
  const summary = document.querySelector(".workspace-summary");
  const aiTarget = document.getElementById("workspace-ai-target");
  const analyzeSplit = document.querySelector('.action-split[data-menu-id="ai-target-menu"]');
  const discoverRow = document.getElementById("discover-query-row");
  const discoverContext = document.getElementById("discover-context");
  const drawerTrigger = document.getElementById("control-drawer-trigger");
  const barMain = document.querySelector(".workspace-bar-main");
  const controlStack = document.querySelector(".workspace-control-stack");
  if(filterGroup) filterGroup.hidden = isDiscoverPanel;
  if(actionGroup) actionGroup.hidden = isDiscoverPanel;
  if(searchWrap) searchWrap.hidden = isDiscoverPanel;
  if(summary) summary.hidden = isDiscoverPanel;
  if(aiTarget) aiTarget.hidden = isDiscoverPanel || isUpdatePanel;
  if(analyzeSplit) analyzeSplit.hidden = isDiscoverPanel || isUpdatePanel;
  if(discoverRow) discoverRow.hidden = !isDiscoverPanel;
  if(discoverContext) discoverContext.hidden = !isDiscoverPanel;
  if(drawerTrigger) drawerTrigger.hidden = isDiscoverPanel;
  if(barMain) barMain.classList.toggle("workspace-bar-main--discover", isDiscoverPanel);
  if(controlStack) controlStack.classList.toggle("workspace-control-stack--discover", isDiscoverPanel);
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
  const introMarkup = renderDiscoverCanvasIntro();
  introNode.hidden = !introMarkup;
  introNode.innerHTML = introMarkup;
  cardsNode.classList.toggle("cards--discover-empty", !discoveryResults().length);
  renderWorkspaceSummaryStrip();
  syncAiTargetUI();
}

function syncControlDrawer(){
  const isDiscoverPanel = panel === DISCOVER_PANEL_KEY;
  const isUpdatePanel = panel === UPDATE_PANEL_KEY;
  const isListPanel = !isDiscoverPanel && !isUpdatePanel;
  const trigger = document.getElementById("control-drawer-trigger");
  const triggerLabel = document.getElementById("control-drawer-label");
  const drawerTitle = document.getElementById("control-drawer-title");
  const drawerSubtitle = document.getElementById("control-drawer-subtitle");
  const listSection = document.getElementById("control-drawer-list");
  const updatesSection = document.getElementById("control-drawer-updates");
  const drawerLabel = isUpdatePanel ? "更新说明" : "筛选";

  if(isDiscoverPanel) closeControlDrawer();
  const drawerVisible = !isDiscoverPanel && isControlDrawerVisible();

  if(triggerLabel) triggerLabel.textContent = drawerLabel;
  if(trigger){
    trigger.classList.toggle("active", drawerVisible);
    trigger.setAttribute("aria-expanded", drawerVisible ? "true" : "false");
  }

  if(drawerTitle){
    drawerTitle.textContent = drawerLabel;
  }
  if(drawerSubtitle){
    drawerSubtitle.textContent = isUpdatePanel
      ? "更新页保持轻量阅读模式，主画布优先展示仓库变化。"
      : "趋势列表和我的库把状态、语言、排序收进抽屉，首屏先看卡片。";
  }

  if(listSection) listSection.hidden = !isListPanel;
  if(updatesSection) updatesSection.hidden = !isUpdatePanel;
}

function syncControlStates(){
  const isUpdatePanel = panel === UPDATE_PANEL_KEY;
  const isDiscoverPanel = panel === DISCOVER_PANEL_KEY;
  const disableListControls = isUpdatePanel || isDiscoverPanel;
  syncWorkspaceBarModes();
  document.getElementById("language").disabled = disableListControls;
  document.querySelectorAll("#state-filter-seg .seg-btn").forEach(btn => { btn.disabled = disableListControls; });
  document.querySelectorAll("#sort-primary-seg .seg-btn").forEach(btn => { btn.disabled = disableListControls; });
  document.getElementById("analyze-visible-btn").disabled = isUpdatePanel || isDiscoverPanel;
  document.getElementById("ai-target-trigger").disabled = isUpdatePanel || isDiscoverPanel;
  const stateFilterGroup = document.getElementById("state-filter-group");
  stateFilterGroup.classList.toggle("is-disabled", disableListControls);
  document.getElementById("sort-primary-group").classList.toggle("is-disabled", disableListControls);
  document.getElementById("clear-updates-menu-item").hidden = !isUpdatePanel || !(userState.favorite_updates || []).length;
  syncCustomSelect("language");
  syncControlDrawer();
}"""
