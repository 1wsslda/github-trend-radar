#!/usr/bin/env python3
from __future__ import annotations

JS = r"""function completedDiscoveryQuery(){
  return discoveryState.last_query || {};
}

function activeOrLastDiscoveryQuery(){
  return (activeDiscoveryJob && activeDiscoveryJob.query) || completedDiscoveryQuery();
}

function currentDiscoveryDraftQuery(){
  const baseQuery = activeOrLastDiscoveryQuery();
  return {
    id:String(discoverDraft.viewId || baseQuery.id || "").trim(),
    query:String(discoverDraft.query || "").trim(),
    limit:currentDiscoveryDraftLimit(),
    auto_expand:!!discoverDraft.autoExpand,
    ranking_profile:normalizeDiscoveryRankingProfile(discoverDraft.rankingProfile || baseQuery.ranking_profile),
  };
}

function isDiscoveryDraftSyncedToLastRun(){
  const draft = currentDiscoveryDraftQuery();
  const completedQuery = normalizeDiscoveryQueryPayload(completedDiscoveryQuery());
  if(!draft.query) return !String(completedQuery.query || "").trim();
  return (
    draft.query === String(completedQuery.query || "").trim()
    && draft.limit === normalizeDiscoveryLimit(completedQuery.limit, currentDiscoveryLimit())
    && draft.auto_expand === (completedQuery.auto_expand !== false)
    && draft.ranking_profile === normalizeDiscoveryRankingProfile(completedQuery.ranking_profile)
  );
}

function currentDiscoveryQueryText(){
  return String(currentDiscoveryDraftQuery().query || "").trim();
}

function currentDiscoveryStatusLabel(){
  if(discoveryBusy) return activeDiscoveryJob?.stage_label || "搜索中";
  if(activeDiscoveryJob?.status === "failed") return "搜索失败";
  if(activeDiscoveryJob?.status === "cancelled") return "已取消";
  if(String(discoverDraft.query || "").trim() && !isDiscoveryDraftSyncedToLastRun()) return "尚未开始";
  if(discoveryResults().length) return "已找到结果";
  if(String(completedDiscoveryQuery().query || "").trim() && discoveryState.last_run_at) return "未找到结果";
  return "尚未开始";
}

function currentDiscoveryAiTargetLabel(){
  if(aiTargets.size === 1){
    const [only] = aiTargets;
    return AI_TARGET_LABELS[only] || AI_TARGET_LABELS.web;
  }
  if(aiTargets.size === 2){
    return [...aiTargets].map(key => AI_TARGET_LABELS[key] || key).join(" + ");
  }
  return `${aiTargets.size} 个 AI`;
}

function currentDiscoveryAutoExpandNote(){
  return discoverDraft.autoExpand ? DISCOVERY_AUTO_EXPAND_NOTE_ON : DISCOVERY_AUTO_EXPAND_NOTE_OFF;
}

function currentDiscoveryViewPayload(name = ""){
  const draftQuery = currentDiscoveryDraftQuery();
  const completedQuery = completedDiscoveryQuery();
  const shouldCarryRunMetadata = !discoveryBusy && isDiscoveryDraftSyncedToLastRun();
  return {
    id:String(draftQuery.id || "").trim(),
    name:String(name || currentDiscoveryQueryText() || "未命名视图").trim(),
    query:String(draftQuery.query || "").trim(),
    limit:Number(draftQuery.limit || currentDiscoveryLimit()) || currentDiscoveryLimit(),
    auto_expand:draftQuery.auto_expand !== false,
    ranking_profile:normalizeDiscoveryRankingProfile(draftQuery.ranking_profile),
    last_run_at:shouldCarryRunMetadata ? String(discoveryState.last_run_at || completedQuery.last_run_at || "").trim() : "",
    last_result_count:shouldCarryRunMetadata ? discoveryResults().length : 0,
  };
}

async function saveCurrentDiscoveryView(){
  const query = currentDiscoveryQueryText();
  if(!query){
    toast("先运行一次搜索，再保存发现视图");
    return;
  }
  const current = currentDiscoveryViewPayload();
  const name = window.prompt("给这个发现视图起个名字：", current.name || query);
  if(name === null) return;
  try{
    const {resp, data} = await requestJson(
      "/api/discovery/views",
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(currentDiscoveryViewPayload(name)),
      },
      "保存发现视图失败",
    );
    if(!resp.ok || !data.ok){
      toast(data.error || "保存发现视图失败");
      return;
    }
    discoveryState = normalizeDiscoveryStatePayload(data.discovery_state || discoveryState);
    render();
    toast(`已保存视图：${String(name || "").trim() || query}`);
  }catch(error){
    toast(error.message || "保存发现视图失败");
  }
}

function applySavedDiscoveryView(viewId){
  const view = savedDiscoveryViews().find(item => item.id === String(viewId || "").trim());
  if(!view) return;
  syncDiscoverDraftFromQuery(view);
  closeMenus();
  render();
}

async function runSavedDiscoveryView(viewId){
  const view = savedDiscoveryViews().find(item => item.id === String(viewId || "").trim());
  if(!view){
    toast("未找到这个发现视图");
    return;
  }
  syncDiscoverDraftFromQuery(view);
  closeMenus();
  await runDiscovery();
}

async function deleteSavedDiscoveryView(viewId){
  const view = savedDiscoveryViews().find(item => item.id === String(viewId || "").trim());
  if(!view){
    toast("未找到这个发现视图");
    return;
  }
  if(!window.confirm(`确认删除发现视图“${view.name}”吗？`)) return;
  try{
    const {resp, data} = await requestJson(
      "/api/discovery/views/delete",
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({id:view.id}),
      },
      "删除发现视图失败",
    );
    if(!resp.ok || !data.ok){
      toast(data.error || "删除发现视图失败");
      return;
    }
    discoveryState = normalizeDiscoveryStatePayload(data.discovery_state || discoveryState);
    render();
    toast(`已删除视图：${view.name}`);
  }catch(error){
    toast(error.message || "删除发现视图失败");
  }
}

function discoveryResultSignature(results){
  if(!Array.isArray(results) || !results.length) return "";
  // Keep this signature aligned with the fields surfaced by discovery top cards and repo cards.
  return results.map(repo => [
    String(repo?.url || ""),
    String(repo?.full_name || ""),
    Number(repo?.rank || 0),
    Number(repo?.composite_score || 0),
    Number(repo?.relevance_score || 0),
    Number(repo?.hot_score || 0),
    Number(repo?.stars || 0),
    Number(repo?.forks || 0),
    String(repo?.language || ""),
    String(repo?.description || ""),
    String(repo?.description_raw || ""),
    String(repo?.cluster_id || ""),
    String(repo?.cluster_label || ""),
    Array.isArray(repo?.match_reasons) ? repo.match_reasons.map(reason => String(reason || "").trim()).join("\u241f") : "",
  ].join("\u241e")).join("\u241d");
}

function renderableDiscoveryResults(job, fallbackResults){
  const fallback = Array.isArray(fallbackResults) ? fallbackResults : [];
  if(!job || typeof job !== "object") return fallback;
  const previewResults = Array.isArray(job.preview_results) ? job.preview_results : [];
  if(String(job.status || "").trim() === "completed"){
    const finalResults = Array.isArray(job.discovery_state?.last_results) ? job.discovery_state.last_results : previewResults;
    return finalResults.length ? finalResults : [];
  }
  if(previewResults.length) return previewResults;
  return fallback;
}

function discoveryProgressEtaLabel(job = activeDiscoveryJob){
  const etaRemainingSeconds = Number(job?.eta_remaining_seconds || 0);
  const etaFullSeconds = Number(job?.eta_full_seconds || 0);
  if(etaRemainingSeconds > 0) return `预计还需 ${etaRemainingSeconds} 秒`;
  if(etaFullSeconds > 0) return `完整结果约 ${etaFullSeconds} 秒`;
  return "正在继续处理";
}
const DISCOVERY_RECENT_QUERY_KEY = "gtr-discover-recent-queries";
const MAX_DISCOVERY_RECENT_QUERIES = 6;
let discoverySuggestionOpen = false;
let discoverySuggestionCloseTimer = 0;

function normalizeRecentDiscoveryQueryItem(payload){
  const raw = payload && typeof payload === "object" ? payload : {};
  const normalized = normalizeDiscoveryQueryPayload(raw);
  if(!String(normalized.query || "").trim()) return null;
  return {
    query:normalized.query,
    limit:normalized.limit,
    auto_expand:normalized.auto_expand !== false,
    ranking_profile:normalizeDiscoveryRankingProfile(normalized.ranking_profile),
    last_run_at:String(raw.last_run_at || normalized.last_run_at || "").trim(),
  };
}

function loadRecentDiscoveryQueries(){
  try{
    const raw = JSON.parse(localStorage.getItem(DISCOVERY_RECENT_QUERY_KEY) || "[]");
    if(!Array.isArray(raw)) return [];
    return raw.map(normalizeRecentDiscoveryQueryItem).filter(Boolean);
  }catch(_err){
    return [];
  }
}

function saveRecentDiscoveryQueries(items){
  localStorage.setItem(DISCOVERY_RECENT_QUERY_KEY, JSON.stringify(items.slice(0, MAX_DISCOVERY_RECENT_QUERIES)));
}

function recentDiscoveryQueries(){
  const merged = [];
  const seen = new Set();
  [rememberedDiscoveryQuery(), ...loadRecentDiscoveryQueries()].forEach(item => {
    const normalized = normalizeRecentDiscoveryQueryItem(item);
    const key = String(normalized?.query || "").trim().toLowerCase();
    if(!key || seen.has(key)) return;
    seen.add(key);
    merged.push(normalized);
  });
  return merged.slice(0, MAX_DISCOVERY_RECENT_QUERIES);
}

function filteredRecentDiscoveryQueries(queryText = String(discoverDraft.query || "").trim()){
  const needle = String(queryText || "").trim().toLowerCase();
  const items = recentDiscoveryQueries();
  if(!needle) return items;
  return items
    .filter(item => String(item.query || "").toLowerCase().includes(needle))
    .slice(0, MAX_DISCOVERY_RECENT_QUERIES);
}

function rememberRecentDiscoveryQuery(payload){
  const normalized = normalizeRecentDiscoveryQueryItem(payload);
  if(!normalized) return;
  const deduped = loadRecentDiscoveryQueries().filter(item => String(item.query || "").toLowerCase() !== normalized.query.toLowerCase());
  saveRecentDiscoveryQueries([normalized, ...deduped]);
}

function closeDiscoverySuggestions(){
  clearTimeout(discoverySuggestionCloseTimer);
  discoverySuggestionCloseTimer = 0;
  discoverySuggestionOpen = false;
  syncDiscoverySuggestionsUI();
}

function scheduleCloseDiscoverySuggestions(delay = 120){
  clearTimeout(discoverySuggestionCloseTimer);
  discoverySuggestionCloseTimer = setTimeout(() => {
    discoverySuggestionOpen = false;
    syncDiscoverySuggestionsUI();
  }, delay);
}

function openDiscoverySuggestions(){
  clearTimeout(discoverySuggestionCloseTimer);
  discoverySuggestionCloseTimer = 0;
  discoverySuggestionOpen = true;
  syncDiscoverySuggestionsUI();
}

function applyRecentDiscoveryQuery(queryText){
  const nextQuery = recentDiscoveryQueries().find(item => item.query === String(queryText || "").trim());
  if(!nextQuery) return;
  syncDiscoverDraftFromQuery(nextQuery);
  discoverySuggestionOpen = false;
  syncDiscoverDraftUI();
  renderWorkspaceSummaryStrip();
  const queryNode = document.getElementById("discover-query");
  if(queryNode){
    queryNode.focus();
    const caret = queryNode.value.length;
    if(typeof queryNode.setSelectionRange === "function") queryNode.setSelectionRange(caret, caret);
  }
}

function syncDiscoverySuggestionsUI(){
  const root = document.getElementById("discover-query-suggest");
  const field = document.querySelector(".discover-query-field");
  const queryNode = document.getElementById("discover-query");
  if(!root || !field || !queryNode) return;

  if(panel !== DISCOVER_PANEL_KEY || discoveryBusy){
    discoverySuggestionOpen = false;
  }

  const items = filteredRecentDiscoveryQueries();
  const heading = String(discoverDraft.query || "").trim() ? "匹配历史搜索" : "最近搜索";
  const shouldShow = panel === DISCOVER_PANEL_KEY && discoverySuggestionOpen && !discoveryBusy && items.length > 0;

  field.classList.toggle("is-open", shouldShow);
  queryNode.setAttribute("aria-expanded", shouldShow ? "true" : "false");
  root.hidden = !shouldShow;
  if(!shouldShow){
    root.innerHTML = "";
    return;
  }

  root.innerHTML = `
    <div class="discover-query-suggest-head">
      <span class="discover-query-suggest-kicker">${h(heading)}</span>
      <span class="discover-query-suggest-note">可直接载入最近一次搜索配置</span>
    </div>
    <div class="discover-query-suggest-list">
      ${items.map(item => `
        <button class="discover-query-suggest-item" type="button" onmousedown="event.preventDefault()" onclick='applyRecentDiscoveryQuery(${JSON.stringify(item.query)})'>
          <span class="discover-query-suggest-title">${h(item.query)}</span>
          <span class="discover-query-suggest-meta">
            <span class="badge">${h(discoveryRankingLabel(item.ranking_profile))}</span>
            ${item.auto_expand ? '<span class="badge gain">自动扩词</span>' : ""}
          </span>
        </button>
      `).join("")}
    </div>
  `;
}

function syncDiscoveryRankingMenuUI(){
  document.querySelectorAll("[data-discovery-ranking]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.discoveryRanking === normalizeDiscoveryRankingProfile(discoverDraft.rankingProfile));
  });
}

function syncDiscoveryContextUI(){
  const limitCopyNode = document.getElementById("discover-limit-copy");
  const autoExpandNoteNode = document.getElementById("discover-auto-expand-note");
  if(limitCopyNode) limitCopyNode.textContent = `结果上限 ${currentDiscoveryDraftLimit()}`;
  if(autoExpandNoteNode) autoExpandNoteNode.textContent = currentDiscoveryAutoExpandNote();
}

function syncDiscoverDraftUI(){
  const queryNode = document.getElementById("discover-query");
  const autoExpandNode = document.getElementById("discover-auto-expand");
  const runNode = document.getElementById("discover-run-btn");
  const runTitleNode = document.getElementById("discover-run-title");
  const runNoteNode = document.getElementById("discover-run-note");
  const rankingTriggerNode = document.getElementById("discover-ranking-trigger");
  const rankingRoot = menuRoot("discover-ranking-menu");
  if(!queryNode) return;

  queryNode.value = discoverDraft.query || "";
  queryNode.disabled = discoveryBusy;
  if(autoExpandNode){
    autoExpandNode.checked = !!discoverDraft.autoExpand;
    autoExpandNode.disabled = discoveryBusy;
  }
  if(rankingTriggerNode) rankingTriggerNode.disabled = discoveryBusy;
  syncDiscoveryRankingMenuUI();
  syncDiscoveryContextUI();
  syncDiscoverySuggestionsUI();

  const hasQuery = !!String(discoverDraft.query || "").trim();
  const canRun = !discoveryBusy && hasQuery;
  if(rankingRoot){
    rankingRoot.classList.toggle("is-idle", !discoveryBusy && !hasQuery);
    rankingRoot.classList.toggle("is-ready", !discoveryBusy && hasQuery);
    rankingRoot.classList.toggle("is-busy", discoveryBusy);
  }
  if(runTitleNode) runTitleNode.textContent = discoveryBusy ? (activeDiscoveryJob?.stage_label || "搜索中") : "开始搜索";
  if(runNoteNode) runNoteNode.textContent = `开始搜索 · ${discoveryRankingLabel(discoverDraft.rankingProfile)}`;
  if(runNode){
    runNode.disabled = !canRun;
  }
  if(panel === DISCOVER_PANEL_KEY) renderWorkspaceSummaryStrip();
}

function renderDiscoveryTop(){
  const top = discoveryResults().slice(0, 3);
  if(!top.length) return "";
  return `<section class="discover-top">
    <div class="group-label">推荐结果</div>
    <div class="discover-top-grid">
      ${top.map(repo => `<article class="discover-top-card">
        <div class="discover-top-rank">#${repo.rank || "-"}</div>
        <div class="discover-chip-title">${h(repo.full_name)}</div>
        <div class="discover-chip-note">综合 ${repo.composite_score || 0} · 相关 ${repo.relevance_score || 0} · 热度 ${repo.hot_score || 0}${repo.cluster_label ? ` · ${h(repo.cluster_label)}` : ""}</div>
        <div class="reason-strip">${(repo.match_reasons || []).slice(0, 2).map(reason => `<span class="reason-pill">${h(reason)}</span>`).join("")}</div>
      </article>`).join("")}
    </div>
  </section>`;
}

function renderSavedDiscoveryViews(){
  const views = savedDiscoveryViews();
  const canSave = !!currentDiscoveryQueryText();
  if(!views.length && !canSave) return "";
  return `<section class="discover-results-toolbar">
    <div class="discover-results-toolbar-main">
      <div class="discover-results-toolbar-pills">
        <span class="summary-strip-item">已保存视图 <strong>${views.length}</strong></span>
      </div>
      <span class="discover-toolbar-note">把一次性搜索保存成可复用的本地发现入口。</span>
    </div>
    <div class="discover-results-toolbar-actions">
      <button class="action-primary" type="button" onclick="saveCurrentDiscoveryView()"${canSave ? "" : " disabled"}>保存当前视图</button>
      ${views.length ? `<div class="menu-wrap" data-menu-id="discover-saved-views-menu">
        <button class="action-quiet menu-toggle" type="button" aria-haspopup="menu" aria-expanded="false" onclick="toggleMenu(event,'discover-saved-views-menu')">已保存视图<span class="menu-caret"></span></button>
        <div class="menu-panel align-right" id="discover-saved-views-menu-panel">
          ${views.map(view => `
            <button class="menu-item" type="button" onclick='runSavedDiscoveryView(${JSON.stringify(view.id)});closeMenus();'>运行 · ${h(view.name)}</button>
            <button class="menu-item" type="button" onclick='applySavedDiscoveryView(${JSON.stringify(view.id)});closeMenus();'>载入配置</button>
            <button class="menu-item" type="button" onclick='deleteSavedDiscoveryView(${JSON.stringify(view.id)});closeMenus();'>删除</button>
            <div class="menu-divider"></div>
          `).join("")}
        </div>
      </div>` : ""}
    </div>
  </section>`;
}

function renderDiscoveryProgress(){
  if(!discoveryBusy || !activeDiscoveryJob) return "";
  const job = activeDiscoveryJob;
  const query = currentDiscoveryQueryText() || "当前关键词";
  const etaLabel = discoveryProgressEtaLabel(job);
  return `<div class="discover-progress-strip" id="discover-progress-strip">
    <div class="discover-progress-copy">
      <span class="discover-progress-stage" id="discover-progress-stage">${h(job.stage_label || "搜索中")}</span>
      <span class="discover-progress-text" id="discover-progress-text">${h(query)}</span>
    </div>
    <div class="discover-progress-actions">
      <span class="discover-progress-eta" id="discover-progress-eta">${h(etaLabel)}</span>
      <button class="action-quiet compact danger" type="button" onclick="cancelDiscovery()">取消</button>
    </div>
  </div>`;
}
function renderDiscoveryFailureCard(){
  const job = activeDiscoveryJob;
  if(!job || job.status !== "failed") return "";
  const diagnostic = String(job.error || job.message || "本次搜索失败").trim();
  return `<div class="discover-feedback-card discover-feedback-card--error">
    <div class="discover-feedback-title">这次搜索没有完成。</div>
    <div class="discover-feedback-copy">可以直接重试，或者先检查网络、Token 和代理设置。</div>
    <div class="discover-feedback-actions">
      <button class="action-primary" type="button" onclick="runDiscovery()">重试本次搜索</button>
      <button class="action-quiet" type="button" onclick="openSettings()">打开设置</button>
    </div>
    <details class="discover-diagnostic">
      <summary>诊断信息</summary>
      <div class="discover-diagnostic-copy">${h(diagnostic)}</div>
    </details>
  </div>`;
}

function renderDiscoveryHint(){
  if(discoveryBusy || (activeDiscoveryJob && activeDiscoveryJob.status === "failed")) return "";
  if(currentDiscoveryStatusLabel() === "未找到结果") return "";
  if(discoveryResults().length) return "";
  return '<div class="discover-inline-hint">输入关键词后开始搜索，结果会显示在下方。</div>';
}

function renderDiscoveryNoResultsNotice(){
  if(currentDiscoveryStatusLabel() !== "未找到结果") return "";
  const query = String(discoveryState.last_query?.query || "").trim();
  return `<div class="discover-inline-hint discover-inline-hint--warning">
    <span>这次没有找到和 <strong>${h(query || "当前关键词")}</strong> 匹配的结果，可以换个关键词或放宽筛选。</span>
    <div class="discover-inline-hint-actions">
      <button class="action-quiet compact" type="button" onclick="runDiscovery()">重新搜索</button>
    </div>
  </div>`;
}

function renderDiscoveryResultsToolbar(){
  const results = discoveryResults();
  if(!results.length) return "";
  const query = activeOrLastDiscoveryQuery();
  const ranking = discoveryRankingLabel(query.ranking_profile || discoverDraft.rankingProfile);
  const rankingDescription = discoveryRankingDescription(query.ranking_profile || discoverDraft.rankingProfile);
  const clusters = discoveryClusters();
  const clusterSummary = clusters.slice(0, 4).map(cluster => `${cluster.label || "未命名"} ${cluster.count || 0}`).join(" · ");
  return `<section class="discover-results-toolbar">
    <div class="discover-results-toolbar-main">
      <div class="discover-results-toolbar-pills">
        <span class="summary-strip-item">候选项目 <strong>${results.length}</strong></span>
        <span class="summary-strip-item">排序方式 <strong>${h(ranking)}</strong></span>
        ${clusters.length ? `<span class="summary-strip-item">主题分组 <strong>${clusters.length}</strong></span>` : ""}
      </div>
      <span class="discover-toolbar-note">${h(clusterSummary || rankingDescription)}</span>
    </div>
    <div class="discover-results-toolbar-actions">
      <button class="action-primary" type="button" onclick="analyzeVisible()">分析这批结果</button>
      <div class="menu-wrap" data-menu-id="discover-result-ai-menu">
        <button class="action-quiet menu-toggle" type="button" aria-haspopup="menu" aria-expanded="false" onclick="toggleMenu(event,'discover-result-ai-menu')">
          AI 目标选择
          <span class="discover-toolbar-ai" data-ai-target-label>${h(currentDiscoveryAiTargetLabel())}</span>
          <span class="menu-caret"></span>
        </button>
        <div class="menu-panel align-right" id="discover-result-ai-menu-panel">
          <button class="menu-item menu-item--check" type="button" data-ai-target="web" onclick="toggleAiTarget('web')">ChatGPT 网页版</button>
          <button class="menu-item menu-item--check" type="button" data-ai-target="desktop" onclick="toggleAiTarget('desktop')">ChatGPT 桌面版</button>
          <button class="menu-item menu-item--check" type="button" data-ai-target="gemini_web" onclick="toggleAiTarget('gemini_web')">Gemini 网页版</button>
          <div class="menu-divider"></div>
          <button class="menu-item menu-item--check" type="button" data-ai-target="copy" onclick="toggleAiTarget('copy')">仅复制提示词</button>
        </div>
      </div>
      <div class="menu-wrap" data-menu-id="discover-result-more-menu">
        <button class="action-quiet menu-toggle" type="button" aria-haspopup="menu" aria-expanded="false" onclick="toggleMenu(event,'discover-result-more-menu')">更多<span class="menu-caret"></span></button>
        <div class="menu-panel align-right" id="discover-result-more-menu-panel">
          <button class="menu-item" type="button" onclick="clearDiscovery();closeMenus();">清空本次结果</button>
        </div>
      </div>
    </div>
  </section>`;
}

function reposForDiscoveryCluster(clusterId){
  const id = String(clusterId || "").trim();
  if(!id) return [];
  const cluster = discoveryClusters().find(item => String(item.id || "").trim() === id) || {};
  const urls = new Set(Array.isArray(cluster.repo_urls) ? cluster.repo_urls.map(url => String(url || "").trim()).filter(Boolean) : []);
  return discoveryResults().filter(repo => String(repo.cluster_id || "").trim() === id || urls.has(String(repo.url || "").trim()));
}

function selectDiscoveryCluster(clusterId){
  const repos = reposForDiscoveryCluster(clusterId);
  if(!repos.length) return;
  selectedUrls = new Set(repos.map(repo => repo.url).filter(Boolean));
  saveSelectedUrls();
  refreshSelectionUI();
  toast(`已选中 ${repos.length} 个主题项目`);
}

function renderDiscoveryClusterMap(){
  const clusters = discoveryClusters().filter(cluster => Number(cluster.count || 0) > 0);
  if(clusters.length < 2) return "";
  const visibleClusters = clusters.slice(0, 6);
  const total = clusters.reduce((sum, cluster) => sum + Number(cluster.count || 0), 0);
  const maxCount = Math.max(1, ...visibleClusters.map(cluster => Number(cluster.count || 0)));
  return `<section class="discover-cluster-map">
    <div class="discover-cluster-map-head">
      <div class="group-label">主题地图</div>
      <div class="discover-chip-note">${clusters.length} 个主题 · ${total} 项</div>
    </div>
    <div class="discover-cluster-map-grid">
      ${visibleClusters.map((cluster, index) => {
        const count = Number(cluster.count || 0);
        const languages = Array.isArray(cluster.languages) ? cluster.languages.filter(Boolean).slice(0, 2).join(" / ") : "";
        const terms = Array.isArray(cluster.top_terms) ? cluster.top_terms.filter(Boolean).slice(0, 3).join(" · ") : "";
        const meta = [count ? `${count} 项` : "", languages, terms].filter(Boolean).join(" · ");
        return `<button class="discover-cluster-node" type="button" onclick='selectDiscoveryCluster(${JSON.stringify(cluster.id)})' style="--cluster-weight:${Math.max(.18, Math.min(1, count / maxCount)).toFixed(3)}">
          <span class="discover-cluster-node-index">${String(index + 1).padStart(2, "0")}</span>
          <span class="discover-cluster-node-main">
            <strong>${h(cluster.label || "未命名主题")}</strong>
            <span>${h(meta || "0 项")}</span>
          </span>
          <span class="discover-cluster-node-action">选中本组</span>
          <span class="discover-cluster-node-bar" aria-hidden="true"></span>
        </button>`;
      }).join("")}
    </div>
  </section>`;
}

function renderDiscoverySelectionBar(){
  const selected = selectedCount();
  if(panel !== DISCOVER_PANEL_KEY || !selected) return "";
  const compareDisabledAttr = selectedRepos().length === 2 ? "" : " disabled";
  return `<section class="discover-selection-bar">
    <div class="discover-selection-meta">
      <span class="summary-strip-item">已选 <strong>${selected}</strong> 项</span>
    </div>
    <div class="discover-selection-actions">
      <button class="action-primary" type="button" onclick="analyzeSelected()">批量分析</button>
      <div class="menu-wrap" data-menu-id="discover-selection-more-menu">
        <button class="action-quiet menu-toggle" type="button" aria-haspopup="menu" aria-expanded="false" onclick="toggleMenu(event,'discover-selection-more-menu')">更多<span class="menu-caret"></span></button>
        <div class="menu-panel align-right" id="discover-selection-more-menu-panel">
          <button class="menu-item" type="button" onclick="openCompareSelected();closeMenus();"${compareDisabledAttr}>对比</button>
          <div class="menu-divider"></div>
          <button class="menu-item" type="button" onclick="batchSetState('favorites');closeMenus();">收藏</button>
          <button class="menu-item" type="button" onclick="batchSetState('watch_later');closeMenus();">稍后看</button>
          <button class="menu-item" type="button" onclick="batchSetState('read');closeMenus();">已读</button>
          <button class="menu-item" type="button" onclick="batchSetState('ignored');closeMenus();">忽略</button>
          <div class="menu-divider"></div>
          <button class="menu-item" type="button" onclick="selectVisible();closeMenus();">重新全选本页</button>
          <button class="menu-item" type="button" onclick="clearSelected();closeMenus();">清空选择</button>
        </div>
      </div>
    </div>
  </section>`;
}

function renderDiscoverCanvasIntro(){
  const sections = [
    renderDiscoveryProgress(),
    renderDiscoveryFailureCard(),
    renderDiscoveryNoResultsNotice(),
    renderDiscoveryHint(),
    renderSavedDiscoveryViews(),
    renderDiscoveryClusterMap(),
    renderDiscoveryTop(),
    renderDiscoveryResultsToolbar(),
    renderDiscoverySelectionBar(),
  ].filter(Boolean);
  return sections.join("");
}

function syncDiscoveryPanel(){
  syncDiscoverDraftUI();
}

function syncDiscoveryLiveStatus(){
  syncDiscoverDraftUI();
  const stageNode = document.getElementById("discover-progress-stage");
  const textNode = document.getElementById("discover-progress-text");
  const etaNode = document.getElementById("discover-progress-eta");
  if(stageNode) stageNode.textContent = activeDiscoveryJob?.stage_label || "搜索中";
  if(textNode) textNode.textContent = currentDiscoveryQueryText() || "当前关键词";
  if(etaNode) etaNode.textContent = discoveryProgressEtaLabel(activeDiscoveryJob);
}
function setDiscoveryRankingProfile(value){
  discoverDraft.viewId = "";
  discoverDraft.limit = currentDiscoveryLimit();
  discoverDraft.rankingProfile = normalizeDiscoveryRankingProfile(value);
  closeMenus();
  syncDiscoverDraftUI();
}

function syncDiscoverDraftFromQuery(lastQuery){
  discoverDraft = {
    viewId:String(lastQuery?.id || "").trim(),
    query:lastQuery?.query || discoverDraft.query,
    limit:normalizeDiscoveryLimit(lastQuery?.limit, currentDiscoveryLimit()),
    autoExpand:lastQuery?.auto_expand !== false,
    rankingProfile:normalizeDiscoveryRankingProfile(lastQuery?.ranking_profile || discoverDraft.rankingProfile),
  };
}

async function startDiscoveryPolling(jobId){
  const pollToken = ++discoveryPollToken;
  while(pollToken === discoveryPollToken){
    let resp;
    let data;
    try{
      ({resp, data} = await requestJson(
        `/api/discovery/job?id=${encodeURIComponent(jobId)}`,
        {cache:"no-store"},
        "读取搜索进度失败",
      ));
    }catch(error){
      discoveryBusy = false;
      discoveryStartedAt = 0;
      activeDiscoveryJob = {
        id:jobId,
        status:"failed",
        stage:"failed",
        stage_label:"进度读取失败",
        message:error.message || "读取搜索进度失败",
        error:error.message || "读取搜索进度失败",
        query:{...discoverDraft},
        warnings:[],
        preview_results:discoveryResults(),
      };
      render();
      toast(error.message || "读取搜索进度失败");
      return;
    }
    if(!resp.ok || !data.ok){
      discoveryBusy = false;
      discoveryStartedAt = 0;
      activeDiscoveryJob = {
        id:jobId,
        status:"failed",
        stage:"failed",
        stage_label:"进度读取失败",
        message:data.error || "读取搜索进度失败",
        error:data.error || "读取搜索进度失败",
        query:{...discoverDraft},
        warnings:[],
        preview_results:discoveryResults(),
      };
      render();
      toast(data.error || "读取搜索进度失败");
      return;
    }
    const job = data.job || null;
    if(!job){
      applyActiveDiscoveryJob(job);
      render();
      return;
    }
    const currentResults = discoveryResults();
    const previousResultsSignature = discoveryResultSignature(currentResults);
    const nextResultsSignature = discoveryResultSignature(renderableDiscoveryResults(job, currentResults));
    const hasTerminalStatus = isTerminalDiscoveryJob(job);
    const shouldRenderResults = hasTerminalStatus || previousResultsSignature !== nextResultsSignature;
    if(job.status === "completed"){
      if(job.discovery_state) discoveryState = job.discovery_state;
      syncDiscoverDraftFromQuery(discoveryState.last_query || job.query || {});
      activeDiscoveryJob = null;
      discoveryBusy = false;
      discoveryStartedAt = 0;
      render();
      toast(`本次搜索已完成（约 ${job.elapsed_seconds || job.eta_full_seconds || "?"} 秒）`);
      return;
    }
    if(job.status === "failed"){
      applyActiveDiscoveryJob(job);
      render();
      toast(job.error || job.message || "本次搜索失败");
      return;
    }
    if(job.status === "cancelled"){
      applyActiveDiscoveryJob(job);
      render();
      toast(job.message || "已取消本次搜索");
      return;
    }
    applyActiveDiscoveryJob(job);
    // Keep discovery cards stable during rescoring; only redraw when the visible result set changes.
    if(shouldRenderResults){
      render();
    }else{
      syncDiscoveryLiveStatus();
    }
    await sleep(900);
  }
}

async function beginDiscoveryJob(endpoint, body, requestError, startMessage){
  panel = DISCOVER_PANEL_KEY;
  localStorage.setItem("gtr-tab", panel);
  discoveryBusy = true;
  discoveryStartedAt = Date.now();
  activeDiscoveryJob = {
    id:"",
    status:"queued",
    stage:"queued",
    stage_label:"等待开始",
    message:startMessage,
    query:{...body},
    warnings:[],
    preview_results:[],
  };
  render();
  try{
    const {resp, data} = await requestJson(
      endpoint,
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(body),
      },
      requestError,
    );
    if(!resp.ok || !data.ok){
      discoveryBusy = false;
      discoveryStartedAt = 0;
      activeDiscoveryJob = null;
      render();
      toast(data.error || requestError);
      return;
    }
    const job = data.job || null;
    if(!job?.id){
      discoveryBusy = false;
      discoveryStartedAt = 0;
      activeDiscoveryJob = null;
      render();
      toast("这次搜索没有返回有效任务");
      return;
    }
    applyActiveDiscoveryJob(job);
    render();
    toast(`${data.message || "搜索已开始"}，首轮约 ${job.eta_initial_seconds || "?"} 秒，完整约 ${job.eta_full_seconds || "?"} 秒`);
    startDiscoveryPolling(job.id);
  }catch(error){
    discoveryBusy = false;
    discoveryStartedAt = 0;
    activeDiscoveryJob = null;
    render();
    toast(error.message || requestError);
  }
}

async function runDiscovery(){
  const payload = {
    id:String(discoverDraft.viewId || "").trim(),
    query:String(discoverDraft.query || "").trim(),
    limit:currentDiscoveryDraftLimit(),
    auto_expand:!!discoverDraft.autoExpand,
    ranking_profile:normalizeDiscoveryRankingProfile(discoverDraft.rankingProfile),
  };
  if(!payload.query){
    toast("请输入关键词");
    return;
  }
  rememberRecentDiscoveryQuery(payload);
  closeDiscoverySuggestions();
  await beginDiscoveryJob("/api/discover", payload, "开始搜索失败", "正在准备这次搜索");
}

async function cancelDiscovery(){
  const jobId = String(activeDiscoveryJob?.id || "").trim();
  if(!jobId){
    toast("当前没有可取消的搜索任务");
    return;
  }
  try{
    const {resp, data} = await requestJson(
      "/api/discovery/cancel",
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({id:jobId}),
      },
      "取消搜索失败",
    );
    if(!resp.ok || !data.ok){
      toast(data.error || "取消搜索失败");
      return;
    }
    if(data.job) applyActiveDiscoveryJob(data.job);
    render();
    toast(data.message || "已发送取消请求");
  }catch(error){
    toast(error.message || "取消搜索失败");
  }
}

async function clearDiscovery(){
  try{
    const {resp, data} = await requestJson("/api/discovery/clear", {method:"POST"}, "清空本次结果失败");
    if(!resp.ok || !data.ok){
      toast(data.error || "清空本次结果失败");
      return;
    }
    discoveryState = data.discovery_state || {};
    activeDiscoveryJob = null;
    discoveryBusy = false;
    discoveryStartedAt = 0;
    render();
    toast(data.message || "已清空本次结果");
  }catch(error){
    toast(error.message || "清空本次结果失败");
  }
}"""
