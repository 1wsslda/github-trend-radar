#!/usr/bin/env python3
from __future__ import annotations

JS = r"""function isOverlayVisible(id){
  return document.getElementById(id)?.classList.contains("show") || false;
}

function isControlDrawerVisible(){
  const drawer = document.getElementById("control-drawer");
  return !!(drawer && !drawer.hidden);
}

function closeControlDrawer(){
  const drawer = document.getElementById("control-drawer");
  if(!drawer) return;
  drawer.hidden = true;
  drawer.classList.remove("show");
  const trigger = document.getElementById("control-drawer-trigger");
  if(trigger){
    trigger.classList.remove("active");
    trigger.setAttribute("aria-expanded", "false");
  }
}

function toggleControlDrawer(force){
  const drawer = document.getElementById("control-drawer");
  if(!drawer) return;
  const nextVisible = typeof force === "boolean" ? force : !isControlDrawerVisible();
  closeMenus();
  drawer.hidden = !nextVisible;
  drawer.classList.toggle("show", nextVisible);
  const trigger = document.getElementById("control-drawer-trigger");
  if(trigger){
    trigger.classList.toggle("active", nextVisible);
    trigger.setAttribute("aria-expanded", nextVisible ? "true" : "false");
  }
}

function syncOverlayLock(){
  const hasVisibleOverlay = OVERLAY_IDS.some(id => document.getElementById(id)?.classList.contains("show"));
  document.body.classList.toggle("overlay-open", hasVisibleOverlay);
}

function setOverlayVisible(id, visible){
  const overlay = document.getElementById(id);
  if(!overlay) return;
  if(visible){
    closeControlDrawer();
    OVERLAY_IDS.forEach(otherId => {
      if(otherId !== id){
        document.getElementById(otherId)?.classList.remove("show");
      }
    });
  }
  overlay.classList.toggle("show", !!visible);
  syncOverlayLock();
}

async function openCompareSelected(){
  const repos = selectedRepos();
  if(repos.length !== 2){
    toast("请先选中 2 个仓库再对比");
    return;
  }
  document.getElementById("compare-body").innerHTML = `<div class="empty">${emptyIcon}<span>正在拉取对比数据...</span></div>`;
  setOverlayVisible("compare-modal", true);
  try{
    const [repoA, repoB] = repos;
    const [detailA, detailB] = await Promise.all([fetchRepoDetails(repoA), fetchRepoDetails(repoB)]);
    comparePrompt = buildComparePrompt(repoA, repoB, detailA, detailB);
    document.getElementById("compare-body").innerHTML = `<div class="notice">对比视图会把两个仓库按同一组维度并排展开，方便从语言、活跃度、README 摘要和项目定位几个层面做快速判断。</div><div class="panel-actions"><button class="action-primary" type="button" onclick="analyzeCompare()">ChatGPT 对比</button></div><div class="compare-grid">${renderCompareCard(repoA, detailA)}${renderCompareCard(repoB, detailB)}</div>`;
  }catch(error){
    comparePrompt = "";
    document.getElementById("compare-body").innerHTML = `<div class="empty">${emptyIcon}<span>${h(error.message || "对比数据加载失败")}</span></div>`;
  }
}

function renderCompareCard(repo, detail){
  const metricMarkup = [
    metricPillMarkup("Stars", `<span class="metric-number">${detail.stars || repo.stars || 0}</span>`),
    metricPillMarkup("Forks", `<span class="metric-number">${detail.forks || repo.forks || 0}</span>`),
    metricPillMarkup("Issues", `<span class="metric-number">${detail.open_issues || 0}</span>`),
    metricPillMarkup("语言", h(repo.language || "未知语言")),
  ].join("");
  return `<article class="compare-card">
    <div class="card-head">
      <div class="card-title-wrap">
        <div class="badges">
          <span class="badge ${gainBadgeClass(repo)}">${h(gainLabel(repo))}</span>
          <span class="badge source">${h(repo.source_label || "GitHub 来源")}</span>
        </div>
        <div class="card-topline">
          <div class="title">${h(repo.full_name)}</div>
        </div>
      </div>
    </div>
    <div class="card-body">
      ${descBlockMarkup(detail.description || detail.description_raw || repo.description || repo.description_raw || "暂无描述")}
      <div class="card-metrics">${metricMarkup}</div>
      <div class="detail-section">
        <div class="section-label">仓库概览</div>
        <div class="detail-grid">
          <div class="detail-item"><strong>License</strong><span>${h(detail.license || "未标注")}</span></div>
          <div class="detail-item"><strong>默认分支</strong><span>${h(detail.default_branch || "未知")}</span></div>
          <div class="detail-item"><strong>最近推送</strong><span>${h(detail.pushed_at || "未知")}</span></div>
          <div class="detail-item"><strong>仓库主页</strong><span>${detail.homepage ? `<a class="link-inline" href="${h(detail.homepage)}" target="_blank" rel="noopener" data-external-url="${h(detail.homepage)}">${h(detail.homepage)}</a>` : "未填写"}</span></div>
        </div>
      </div>
      <div class="detail-section">
        <div class="section-label">README 摘要</div>
        <div class="readme-block">${h(detail.readme_summary || detail.readme_summary_raw || "暂无 README 摘要")}</div>
      </div>
      <div class="card-utility-actions">
        <a class="action-quiet compact" href="${h(repo.url)}" target="_blank" rel="noopener" data-external-url="${h(repo.url)}">打开 GitHub</a>
      </div>
    </div>
  </article>`;
}

async function analyzeCompare(){
  if(!comparePrompt){
    toast("当前没有可分析的对比内容");
    return;
  }
  await openAiPrompts([comparePrompt]);
}

let tokenStatusRequestId = 0;

function applyTokenStatus(status){
  const node = document.getElementById("setting-token-status");
  if(!node) return;
  const clean = status && typeof status === "object" ? status : {};
  const state = String(clean.state || "idle").trim() || "idle";
  node.dataset.state = state;
  node.textContent = String(clean.message || "会自动校验当前 Token，可区分空值、无效、权限不足和可正常使用四种状态。");
}

async function validateTokenStatus(tokenOverride){
  const requestId = ++tokenStatusRequestId;
  applyTokenStatus({state:"checking", message:"正在校验 GitHub Token..."});
  try{
    const {resp, data} = await requestJson(
      "/api/settings/token-status",
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({github_token:typeof tokenOverride === "string" ? tokenOverride : (document.getElementById("setting-token")?.value || "")}),
      },
      "校验 GitHub Token 失败",
    );
    if(requestId !== tokenStatusRequestId) return null;
    if(!resp.ok || !data.ok){
      applyTokenStatus({state:"invalid", message:data.error || "校验 GitHub Token 失败"});
      return null;
    }
    applyTokenStatus(data.status || null);
    return data.status || null;
  }catch(error){
    if(requestId !== tokenStatusRequestId) return null;
    applyTokenStatus({state:"invalid", message:error.message || "校验 GitHub Token 失败"});
    return null;
  }
}

async function openSettings(){
  try{
    const {resp, data} = await requestJson("/api/settings", {cache:"no-store"}, "读取设置失败");
    if(resp.ok) settings = data;
  }catch(_err){}
  document.getElementById("setting-token").value = settings.github_token || "";
  document.getElementById("setting-proxy").value = settings.proxy || "";
  document.getElementById("setting-refresh-hours").value = settings.refresh_hours || 1;
  document.getElementById("setting-result-limit").value = settings.result_limit || 25;
  document.getElementById("setting-port").value = settings.port || 8080;
  document.getElementById("setting-auto-start").checked = !!settings.auto_start;
  document.getElementById("settings-runtime-hint").textContent = `当前生效端口 ${settings.effective_port || settings.port || 8080} · 当前代理 ${settings.effective_proxy || "未启用"} · 关闭主窗口时会直接退出程序 · 程序不提供 VPN${settings.restart_required ? " · 修改端口后需重启生效" : ""}`;
  setOverlayVisible("settings-modal", true);
  validateTokenStatus(settings.github_token || "");
}

function closeSettings(){
  setOverlayVisible("settings-modal", false);
}

async function saveSettings(){
  const payload = {
    github_token:document.getElementById("setting-token").value,
    proxy:document.getElementById("setting-proxy").value,
    refresh_hours:Number(document.getElementById("setting-refresh-hours").value || 1),
    result_limit:Number(document.getElementById("setting-result-limit").value || 25),
    port:Number(document.getElementById("setting-port").value || 8080),
    auto_start:document.getElementById("setting-auto-start").checked,
    default_sort:sortPrimary,
  };
  try{
    const {resp, data} = await requestJson(
      "/api/settings",
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(payload),
      },
      "保存设置失败",
    );
    if(!resp.ok || !data.ok){
      toast(data.error || "保存失败");
      return;
    }
    settings = data.settings;
    toast(data.message || "设置已保存");
    closeSettings();
  }catch(error){
    toast(error.message || "保存设置失败");
  }
}

async function openDetail(owner, name, label){
  setOverlayVisible("detail-modal", true);
  document.getElementById("detail-title").textContent = label;
  document.getElementById("detail-body").innerHTML = `<div class="empty">${emptyIcon}<span>正在拉取仓库详情...</span></div>`;
  try{
    const detail = await fetchRepoDetails({owner, name});
    const topics = Array.isArray(detail.topics) ? detail.topics.filter(Boolean) : [];
    const metricMarkup = [
      metricPillMarkup("Stars", `<span class="metric-number">${detail.stars || 0}</span>`),
      metricPillMarkup("Forks", `<span class="metric-number">${detail.forks || 0}</span>`),
      metricPillMarkup("Watchers", `<span class="metric-number">${detail.watchers || 0}</span>`),
      metricPillMarkup("Issues", `<span class="metric-number">${detail.open_issues || 0}</span>`),
    ].join("");
    document.getElementById("detail-body").innerHTML = `<div class="detail-hero"><div class="badges"><span class="badge source">${h(detail.license || "未标注 License")}</span><span class="badge source">${h(detail.default_branch || "未知分支")}</span>${detail.homepage ? `<a class="badge source" href="${h(detail.homepage)}" target="_blank" rel="noopener" data-external-url="${h(detail.homepage)}">Homepage</a>` : ""}</div><div class="readme-block">${h(detail.description || detail.description_raw || "暂无简介")}</div><div class="card-metrics">${metricMarkup}</div></div><div class="detail-section"><div class="section-label">仓库概览</div><div class="detail-grid"><div class="detail-item"><strong>仓库</strong><span>${h(detail.full_name || label)}</span></div><div class="detail-item"><strong>最近推送</strong><span>${h(detail.pushed_at || "未知")}</span></div><div class="detail-item"><strong>最后更新</strong><span>${h(detail.updated_at || "未知")}</span></div><div class="detail-item"><strong>默认分支</strong><span>${h(detail.default_branch || "未知")}</span></div><div class="detail-item"><strong>License</strong><span>${h(detail.license || "未标注")}</span></div><div class="detail-item"><strong>主页</strong><span>${detail.homepage ? `<a class="link-inline" href="${h(detail.homepage)}" target="_blank" rel="noopener" data-external-url="${h(detail.homepage)}">${h(detail.homepage)}</a>` : "未填写"}</span></div></div></div><div class="detail-section"><div class="section-label">README 摘要</div><div class="readme-block">${h(detail.readme_summary || detail.readme_summary_raw || "暂无 README 摘要")}</div></div>${topics.length ? `<div class="detail-section"><div class="section-label">Topics</div><div class="topic-list">${topics.map(topic => `<span class="topic">${h(topic)}</span>`).join("")}</div></div>` : ""}<div class="panel-actions"><a class="action-quiet" href="${h(detail.html_url || "#")}" target="_blank" rel="noopener" data-external-url="${h(detail.html_url || "#")}">打开 GitHub</a></div>`;
  }catch(error){
    document.getElementById("detail-body").innerHTML = `<div class="empty">${emptyIcon}<span>${h(error.message || "详情获取失败")}</span></div>`;
  }
}

function openDetailFromRecord(fullName, url){
  const repo = repoByUrl(url) || (() => {
    const parts = String(fullName || "").split("/");
    return {full_name:fullName, owner:parts[0] || "", name:parts[1] || ""};
  })();
  if(!repo.owner || !repo.name){
    toast("缺少仓库标识");
    return;
  }
  openDetail(repo.owner, repo.name, repo.full_name || fullName);
}

function closeDetail(){
  setOverlayVisible("detail-modal", false);
}

function closeCompare(){
  setOverlayVisible("compare-modal", false);
}"""
