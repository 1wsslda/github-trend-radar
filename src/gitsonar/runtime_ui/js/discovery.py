#!/usr/bin/env python3
from __future__ import annotations

JS = r"""function currentDiscoveryQuery(){
  return (activeDiscoveryJob && activeDiscoveryJob.query) || discoveryState.last_query || {};
}

function currentDiscoveryQueryText(){
  return String(currentDiscoveryQuery().query || discoverDraft.query || "").trim();
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

function syncDiscoverDraftUI(){
  const queryNodes = [
    document.getElementById("discover-query"),
    document.getElementById("discover-query-drawer"),
  ].filter(Boolean);
  const languageNode = document.getElementById("discover-language");
  const limitNode = document.getElementById("discover-limit");
  const rankingProfileNode = document.getElementById("discover-ranking-profile");
  const autoExpandNode = document.getElementById("discover-auto-expand");
  const saveQueryNode = document.getElementById("discover-save-query");
  const clearNode = document.getElementById("discover-clear-btn");
  const rankingMetaNode = document.getElementById("discover-ranking-profile-meta");
  const runNodes = [
    document.getElementById("discover-run-btn"),
    document.getElementById("discover-run-drawer-btn"),
  ].filter(Boolean);
  if(!queryNodes.length) return;

  queryNodes.forEach(node => {
    node.value = discoverDraft.query || "";
    node.disabled = discoveryBusy;
  });
  if(languageNode){
    languageNode.value = discoverDraft.language || "";
    languageNode.disabled = discoveryBusy;
  }
  if(limitNode){
    limitNode.value = discoverDraft.limit || 20;
    limitNode.disabled = discoveryBusy;
  }
  if(rankingProfileNode){
    rankingProfileNode.value = normalizeDiscoveryRankingProfile(discoverDraft.rankingProfile);
    rankingProfileNode.disabled = discoveryBusy;
  }
  if(autoExpandNode){
    autoExpandNode.checked = !!discoverDraft.autoExpand;
    autoExpandNode.disabled = discoveryBusy;
  }
  if(saveQueryNode){
    saveQueryNode.checked = !!discoverDraft.saveQuery;
    saveQueryNode.disabled = discoveryBusy;
  }
  if(rankingMetaNode){
    rankingMetaNode.textContent = discoveryRankingDescription(discoverDraft.rankingProfile);
  }
  syncCustomSelect("discover-ranking-profile");

  if(clearNode){
    clearNode.disabled = discoveryBusy || (!discoveryResults().length && !discoveryState.last_query?.query);
  }

  const runLabel = discoveryBusy ? (activeDiscoveryJob?.stage_label || "搜索中") : "开始搜索";
  const canRun = !discoveryBusy && !!String(discoverDraft.query || "").trim();
  runNodes.forEach(node => {
    node.disabled = !canRun;
    node.textContent = runLabel;
  });
}

function renderSavedDiscoveryQueries(){
  const items = savedDiscoveryQueries();
  if(!items.length){
    return '<div class="discover-saved-empty">还没有保存的搜索。</div>';
  }
  const disabledAttr = discoveryBusy ? " disabled" : "";
  return items.map(item => `<div class="discover-chip">
    <div class="discover-chip-head">
      <div class="discover-chip-title">${h(item.query)}</div>
      ${item.language ? `<span class="badge source">${h(item.language)}</span>` : ""}
      <span class="badge">${h(discoveryRankingLabel(item.ranking_profile))}</span>
      ${item.auto_expand ? '<span class="badge gain">已扩词</span>' : ""}
    </div>
    <div class="discover-chip-note">${h(item.last_run_at ? `上次运行 ${item.last_run_at}` : "尚未运行")}</div>
    <div class="discover-chip-actions">
      <button class="action-quiet compact" type="button" onclick='runSavedDiscovery(${JSON.stringify(item.id)})'${disabledAttr}>运行</button>
      <button class="action-quiet compact danger" type="button" onclick='deleteDiscoveryQuery(${JSON.stringify(item.id)})'${disabledAttr}>删除</button>
    </div>
  </div>`).join("");
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
        <div class="discover-chip-note">综合 ${repo.composite_score || 0} · 相关 ${repo.relevance_score || 0} · 热度 ${repo.hot_score || 0}</div>
        <div class="reason-strip">${(repo.match_reasons || []).slice(0, 2).map(reason => `<span class="reason-pill">${h(reason)}</span>`).join("")}</div>
      </article>`).join("")}
    </div>
  </section>`;
}

function renderDiscoveryProgress(){
  if(!discoveryBusy || !activeDiscoveryJob) return "";
  const job = activeDiscoveryJob;
  const query = currentDiscoveryQueryText() || "当前关键词";
  const etaRemainingSeconds = Number(job.eta_remaining_seconds || 0);
  const etaFullSeconds = Number(job.eta_full_seconds || 0);
  const etaLabel = etaRemainingSeconds > 0
    ? `预计还需 ${etaRemainingSeconds} 秒`
    : (etaFullSeconds > 0 ? `完整结果约 ${etaFullSeconds} 秒` : "正在继续处理");
  return `<div class="discover-progress-strip">
    <div class="discover-progress-copy">
      <span class="discover-progress-stage">${h(job.stage_label || "搜索中")}</span>
      <span class="discover-progress-text">${h(query)}</span>
    </div>
    <div class="discover-progress-actions">
      <span class="discover-progress-eta">${h(etaLabel)}</span>
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
  if(discoveryResults().length) return "";
  return '<div class="discover-inline-hint">输入关键词后开始搜索，结果会显示在下方。</div>';
}

function renderDiscoveryResultsToolbar(){
  const results = discoveryResults();
  if(!results.length) return "";
  const ranking = discoveryRankingLabel(currentDiscoveryQuery().ranking_profile || discoverDraft.rankingProfile);
  const rankingDescription = discoveryRankingDescription(currentDiscoveryQuery().ranking_profile || discoverDraft.rankingProfile);
  return `<section class="discover-results-toolbar">
    <div class="discover-results-toolbar-main">
      <span class="summary-strip-item">候选项目 <strong>${results.length}</strong></span>
      <span class="summary-strip-item">排序方式 <strong>${h(ranking)}</strong></span>
      <span class="discover-toolbar-note">${h(rankingDescription)}</span>
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
    renderDiscoveryHint(),
    renderDiscoveryTop(),
    renderDiscoveryResultsToolbar(),
    renderDiscoverySelectionBar(),
  ].filter(Boolean);
  return sections.join("");
}

function syncDiscoveryPanel(){
  const savedNode = document.getElementById("discover-saved");
  const savedSummaryNote = document.querySelector(".discover-saved-summary-note");
  if(!savedNode) return;
  syncDiscoverDraftUI();
  savedNode.innerHTML = renderSavedDiscoveryQueries();
  if(savedSummaryNote){
    const count = savedDiscoveryQueries().length;
    savedSummaryNote.textContent = count ? `最近 ${Math.min(count, 5)} 条` : "还没有保存";
  }
}

function syncDiscoverDraftFromQuery(lastQuery){
  discoverDraft = {
    query:lastQuery?.query || discoverDraft.query,
    language:lastQuery?.language || "",
    limit:lastQuery?.limit || discoverDraft.limit || 20,
    autoExpand:lastQuery?.auto_expand !== false,
    rankingProfile:normalizeDiscoveryRankingProfile(lastQuery?.ranking_profile || discoverDraft.rankingProfile),
    saveQuery:false,
  };
  saveDiscoverDraft();
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
    applyActiveDiscoveryJob(job);
    render();
    if(!job) return;
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
      discoveryBusy = false;
      discoveryStartedAt = 0;
      render();
      toast(job.error || job.message || "本次搜索失败");
      return;
    }
    if(job.status === "cancelled"){
      discoveryBusy = false;
      discoveryStartedAt = 0;
      render();
      toast(job.message || "已取消本次搜索");
      return;
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
    query:String(discoverDraft.query || "").trim(),
    language:String(discoverDraft.language || "").trim(),
    limit:Number(discoverDraft.limit || 20),
    auto_expand:!!discoverDraft.autoExpand,
    ranking_profile:normalizeDiscoveryRankingProfile(discoverDraft.rankingProfile),
    save_query:!!discoverDraft.saveQuery,
  };
  if(!payload.query){
    toast("请输入关键词");
    return;
  }
  await beginDiscoveryJob("/api/discover", payload, "开始搜索失败", "正在准备这次搜索");
}

async function runSavedDiscovery(queryId){
  await beginDiscoveryJob("/api/discovery/run-saved", {id:queryId}, "运行保存搜索失败", "正在重新运行已保存搜索");
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

async function deleteDiscoveryQuery(queryId){
  if(!window.confirm("确认删除这条保存的搜索吗？")) return;
  try{
    const {resp, data} = await requestJson(
      "/api/discovery/delete",
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({id:queryId}),
      },
      "删除保存搜索失败",
    );
    if(!resp.ok || !data.ok){
      toast(data.error || "删除保存搜索失败");
      return;
    }
    discoveryState = data.discovery_state || {};
    render();
    toast(data.message || "已删除保存的搜索");
  }catch(error){
    toast(error.message || "删除保存搜索失败");
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
