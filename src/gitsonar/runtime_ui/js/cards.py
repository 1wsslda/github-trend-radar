#!/usr/bin/env python3
from __future__ import annotations

JS = r"""const emptyIcon = '<div style="display:flex; flex-direction:column; align-items:center; gap:24px; padding:64px 20px;"><div style="position:relative; width:80px; height:80px; border-radius:999px; background:radial-gradient(circle at center, rgba(233,201,143,0.08) 0%, transparent 70%); display:flex; align-items:center; justify-content:center;"><svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="rgba(233,201,143,0.24)" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M16 16s-1.5-2-4-2-4 2-4 2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line></svg></div></div>';

function selectedBadgeMarkup(index){
  return `<span class="badge badge-selection">#${index + 1} 已选</span>`;
}

function repoInState(stateKey, url){
  return !!((userState[stateKey] || []).includes(url));
}

function stableMenuId(prefix, value){
  const normalized = String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(-48);
  return `${prefix}-${normalized || "item"}`;
}

function metricPillMarkup(label, value){
  return `<span class="meta-pill"><strong>${h(label)}</strong><span>${value}</span></span>`;
}

function repoStateActionsMarkup(repo){
  if(!repo || !repo.url) return "";
  const primaryActions = stateDefs().filter(state => PRIMARY_STATE_KEYS.has(state.key)).map(state => {
    const active = repoInState(state.key, repo.url);
    return `<button class="state-chip ${active ? "active" : ""}" type="button" aria-pressed="${active ? "true" : "false"}" onclick='toggleState(${JSON.stringify(state.key)}, ${JSON.stringify(repo.url)})'>${h(state.label)}</button>`;
  }).join("");
  const secondaryActions = stateDefs().filter(state => !PRIMARY_STATE_KEYS.has(state.key));
  if(!secondaryActions.length) return primaryActions;
  const menuId = stableMenuId("repo-state", repo.url || repo.full_name);
  const secondaryMarkup = secondaryActions.map(state => {
    const active = repoInState(state.key, repo.url);
    return `<button class="menu-item${active ? " active" : ""}" type="button" onclick='toggleState(${JSON.stringify(state.key)}, ${JSON.stringify(repo.url)});closeMenus();'>${h(state.label)}</button>`;
  }).join("");
  return `${primaryActions}
    <div class="menu-wrap" data-menu-id="${h(menuId)}">
      <button class="action-quiet compact menu-toggle state-more-toggle" type="button" aria-haspopup="menu" aria-expanded="false" onclick='toggleMenu(event, ${JSON.stringify(menuId)})'>更多<span class="menu-caret"></span></button>
      <div class="menu-panel align-left" id="${h(menuId)}-panel">
        ${secondaryMarkup}
      </div>
    </div>`;
}

function cardsByUrl(url){
  const matches = [];
  document.querySelectorAll("[data-select-url]").forEach(card => {
    if(card.getAttribute("data-select-url") === url) matches.push(card);
  });
  return matches;
}

function syncStateActionsForUrl(url){
  const repo = repoByUrl(url) || synthesizeRepoFromUpdate(updateByUrl(url));
  if(!repo) return;
  cardsByUrl(url).forEach(card => {
    const actions = card.querySelector(".card-state-actions");
    if(actions) actions.innerHTML = repoStateActionsMarkup(repo);
  });
}

function descBlockMarkup(text, muted = false){
  const safe = h(text || "暂无描述");
  return `<div class="desc-wrap"><div class="desc${muted ? " muted" : ""}">${safe}</div><div class="desc-popover${muted ? " muted" : ""}">${safe}</div></div>`;
}

function refreshSelectionSummary(){
  const isUpdatePanel = panel === UPDATE_PANEL_KEY;
  const isDiscoverPanel = panel === DISCOVER_PANEL_KEY;
  const repos = visibleRepos();
  const updates = visibleUpdates();
  const selected = selectedCount();
  document.getElementById("visible-count").textContent = isUpdatePanel ? updates.length : repos.length;
  document.getElementById("visible-label").textContent = isUpdatePanel ? " 条更新" : (isDiscoverPanel ? " 个候选项目" : " 个仓库");
  document.getElementById("selected-count").textContent = selected;
  const batchDockCount = document.getElementById("batch-dock-count");
  const compareSelectedBtn = document.getElementById("compare-selected-btn");
  const batchDock = document.getElementById("batch-dock");
  if(batchDockCount) batchDockCount.textContent = selected;
  if(compareSelectedBtn) compareSelectedBtn.disabled = selectedRepos().length !== 2;
  const showBatchDock = !isDiscoverPanel && selected > 0;
  if(batchDock) batchDock.classList.toggle("show", showBatchDock);
  document.body.classList.toggle("has-batch-dock", showBatchDock);
}

function syncCardSelectionState(){
  const urlArray = [...selectedUrls];
  document.querySelectorAll("[data-select-url]").forEach(card => {
    const url = card.getAttribute("data-select-url");
    const selectedIdx = urlArray.indexOf(url);
    const selected = selectedIdx !== -1;
    card.classList.toggle("selected", selected);
    const badgeRow = card.querySelector(".badges");
    const existingBadge = badgeRow?.querySelector(".badge-selection");
    const markup = selectedBadgeMarkup(selectedIdx);
    if(selected){
      if(!existingBadge && badgeRow){
        badgeRow.insertAdjacentHTML("afterbegin", markup);
      }else if(existingBadge && existingBadge.outerHTML !== markup){
        existingBadge.outerHTML = markup;
      }
    }else if(existingBadge){
      existingBadge.remove();
    }
  });
}

function refreshSelectionUI(){
  refreshSelectionSummary();
  syncCardSelectionState();
  if(panel === DISCOVER_PANEL_KEY){
    syncWorkspaceCanvas();
    syncAiTargetUI();
  }
}

function renderRepoCards(repos, isChunk = false){
  if(!repos.length) return (isChunk ? "" : `<div class="empty">${emptyIcon}<span>当前面板没有匹配结果。</span></div>`);
  const urlArray = [...selectedUrls];
  return repos.map(repo => {
    const selectedIdx = urlArray.indexOf(repo.url);
    const selected = selectedIdx !== -1;
    const descriptionText = repo.description || repo.description_raw || "暂无描述";
    const isDiscoverCard = panel === DISCOVER_PANEL_KEY;
    const badgeMarkup = isDiscoverCard
      ? `${selected ? selectedBadgeMarkup(selectedIdx) : ""}
         <span class="badge gain">综合 ${repo.composite_score || 0}</span>
         <span class="badge source">相关 ${repo.relevance_score || 0}</span>
         <span class="badge source">热度 ${repo.hot_score || 0}</span>`
      : `${selected ? selectedBadgeMarkup(selectedIdx) : ""}
         <span class="badge ${gainBadgeClass(repo)}">${h(gainLabel(repo))}</span>
         <span class="badge source">${h(repo.source_label || "GitHub 来源")}</span>`;
    const reasonMarkup = isDiscoverCard && (repo.match_reasons || []).length
      ? `<div class="reason-strip">${(repo.match_reasons || []).map(reason => `<span class="reason-pill">${h(reason)}</span>`).join("")}</div>`
      : "";
    const metricMarkup = [
      metricPillMarkup("Stars", `<span class="metric-number">${repo.stars || 0}</span>`),
      metricPillMarkup("Forks", `<span class="metric-number">${repo.forks || 0}</span>`),
      metricPillMarkup("语言", h(repo.language || "未知语言")),
    ].join("");
    return `<article class="card selectable ${selected ? "selected" : ""}" data-select-url="${h(repo.url)}" tabindex="0">
      <div class="card-head">
        <div class="card-title-wrap">
          <div class="card-meta-row">
            <div class="badges">
              ${badgeMarkup}
            </div>
            <div class="card-metrics">${metricMarkup}</div>
          </div>
          <div class="card-topline">
            <a class="title" href="${h(repo.url)}" target="_blank" rel="noopener" data-external-url="${h(repo.url)}">${h(repo.full_name)}</a>
            <div class="meta-rank">#${repo.rank || "-"}</div>
          </div>
        </div>
      </div>
      <div class="card-body">
        ${descBlockMarkup(descriptionText)}
        ${reasonMarkup}
        <div class="card-footer">
          <div class="card-state-row">
            <div class="card-state-actions">${repoStateActionsMarkup(repo)}</div>
            <div class="card-utility-actions">
              <button class="action-quiet compact" type="button" onclick='analyzeRepo(${JSON.stringify(repo.url)})'>分析</button>
              <button class="action-quiet compact" type="button" onclick='openDetail(${JSON.stringify(repo.owner)}, ${JSON.stringify(repo.name)}, ${JSON.stringify(repo.full_name)})'>详情</button>
            </div>
          </div>
        </div>
      </div>
    </article>`;
  }).join("");
}

function renderUpdateCards(items, isChunk = false){
  if(!items.length) return (isChunk ? "" : `<div class="empty">${emptyIcon}<span>收藏仓库最近还没有检测到新的变化。</span></div>`);
  const urlArray = [...selectedUrls];
  return items.map(update => {
    const selectedIdx = urlArray.indexOf(update.url);
    const selected = selectedIdx !== -1;
    const changeBadges = (update.changes || []).map(change => `<span class="badge gain">${h(change)}</span>`).join("");
    const summary = (update.changes || []).length ? (update.changes || []).join(" · ") : "最近一次检测没有整理出可展示的变化摘要。";
    const repo = repoByUrl(update.url) || synthesizeRepoFromUpdate(update);
    const metricMarkup = [
      metricPillMarkup("Stars", `<span class="metric-number">${update.stars || 0}</span>`),
      metricPillMarkup("Forks", `<span class="metric-number">${update.forks || 0}</span>`),
      metricPillMarkup("Pushed", h(update.pushed_at || "未知")),
    ].join("");
    return `<article class="update-card selectable ${selected ? "selected" : ""}" data-select-url="${h(update.url)}" tabindex="0">
      <div class="card-head">
        <div class="card-title-wrap">
          <div class="card-meta-row">
            <div class="badges">
              ${selected ? selectedBadgeMarkup(selectedIdx) : ""}
              <span class="badge source">收藏更新</span>
              ${update.latest_release_tag ? `<span class="badge source">${h(update.latest_release_tag)}</span>` : ""}
            </div>
            <div class="card-metrics">${metricMarkup}</div>
          </div>
          <div class="card-topline">
            <a class="title" href="${h(update.url)}" target="_blank" rel="noopener" data-external-url="${h(update.url)}">${h(update.full_name)}</a>
            <div class="meta-rank">${h(update.checked_at || "最近检查时间未知")}</div>
          </div>
        </div>
      </div>
      <div class="card-body">
        ${changeBadges ? `<div class="badges">${changeBadges}</div>` : ""}
        ${descBlockMarkup(summary)}
        <div class="card-footer">
          <div class="card-state-row">
            <div class="card-state-actions">${repoStateActionsMarkup(repo)}</div>
            <div class="card-utility-actions">
              <button class="action-quiet compact" type="button" onclick='analyzeRepo(${JSON.stringify(update.url)})'>分析</button>
              <button class="action-quiet compact" type="button" onclick='openDetailFromRecord(${JSON.stringify(update.full_name)}, ${JSON.stringify(update.url)})'>详情</button>
            </div>
          </div>
        </div>
      </div>
    </article>`;
  }).join("");
}

function refreshVisibleCards(){
  const isUpdatePanel = panel === UPDATE_PANEL_KEY;
  const isDiscoverPanel = panel === DISCOVER_PANEL_KEY;
  const data = isUpdatePanel ? visibleUpdates() : visibleRepos();
  const renderFn = isUpdatePanel ? renderUpdateCards : renderRepoCards;

  window.__lazyData = data;
  window.__lazyRenderFn = renderFn;
  window.__lazyIndex = 30;

  const container = document.getElementById("cards");
  container.innerHTML = isDiscoverPanel && !data.length ? "" : renderFn(data.slice(0, window.__lazyIndex));
  if(window.__lazyObserver){
    window.__lazyObserver.disconnect();
  }

  if(window.__lazyData.length > window.__lazyIndex){
    container.insertAdjacentHTML("beforeend", '<div id="lazy-sentinel" style="height:40px;"></div>');
    window.__lazyObserver = new IntersectionObserver((entries) => {
      if(entries[0].isIntersecting) {
        const sentinel = document.getElementById("lazy-sentinel");
        if(sentinel) sentinel.remove();

        const nextChunk = window.__lazyData.slice(window.__lazyIndex, window.__lazyIndex + 30);
        window.__lazyIndex += 30;

        if(nextChunk.length) {
          container.insertAdjacentHTML("beforeend", window.__lazyRenderFn(nextChunk, true));
        }
        if(window.__lazyData.length > window.__lazyIndex) {
          container.insertAdjacentHTML("beforeend", '<div id="lazy-sentinel" style="height:40px;"></div>');
          const nextSentinel = document.getElementById("lazy-sentinel");
          if(nextSentinel) window.__lazyObserver.observe(nextSentinel);
        }
      }
    }, { rootMargin: "200px" });
    window.__lazyObserver.observe(document.getElementById("lazy-sentinel"));
  }
}

function render(){
  cleanupSelected();
  ensureValidPanel();
  const isUpdatePanel = panel === UPDATE_PANEL_KEY;
  const isDiscoverPanel = panel === DISCOVER_PANEL_KEY;
  document.getElementById("note").textContent = currentNote || "已显示最新数据";

  const languageSource = (!isUpdatePanel && !isDiscoverPanel) ? panelRepoSource() : [];
  const languages = [...new Set(languageSource.map(repo => repo.language).filter(Boolean))]
    .sort((a, b) => String(a).localeCompare(String(b), "zh-Hans-CN"));
  const languageNode = document.getElementById("language");
  languageNode.innerHTML = '<option value="">全部语言</option>' + languages.map(language => `<option value="${h(language)}">${h(language)}</option>`).join("");
  languageNode.value = languages.includes(languageFilter) ? languageFilter : "";
  languageFilter = languageNode.value;
  renderTabs();

  const repos = visibleRepos();
  const updates = visibleUpdates();

  window.__lazyData = isUpdatePanel ? updates : repos;
  window.__lazyRenderFn = isUpdatePanel ? renderUpdateCards : renderRepoCards;
  window.__lazyIndex = 30;
  refreshVisibleCards();

  syncStateFilterUI();
  syncSortUI();
  syncAiTargetUI();
  syncControlStates();
  syncDiscoveryPanel();
  syncAllCustomSelects();
  syncWorkspaceHeader();
  syncWorkspaceCanvas();
  document.getElementById("analyze-visible-btn").querySelector(".split-main-title").textContent = isDiscoverPanel ? "分析这批结果" : "分析当前列表";
  refreshSelectionSummary();
}

function setPanel(nextPanel){
  panel = normalizePanelKey(nextPanel || "daily");
  localStorage.setItem("gtr-tab", panel);
  closeMenus();
  closeControlDrawer();
  render();
}

function toggleSelected(url){
  if(selectedUrls.has(url)) selectedUrls.delete(url);
  else selectedUrls.add(url);
  saveSelectedUrls();
  refreshSelectionUI();
}

function clearSelected(){
  if(!selectedUrls.size){
    toast("当前没有已选条目");
    return;
  }
  selectedUrls.clear();
  saveSelectedUrls();
  refreshSelectionUI();
  toast("已清空选择");
}

function selectVisible(){
  const urls = visibleLinkList();
  if(!urls.length){
    toast(panel === UPDATE_PANEL_KEY ? "当前面板没有可选中的更新" : "当前面板没有可选中的仓库");
    return;
  }
  urls.forEach(url => selectedUrls.add(url));
  saveSelectedUrls();
  refreshSelectionUI();
  toast(`已选中 ${urls.length} 项`);
}"""
