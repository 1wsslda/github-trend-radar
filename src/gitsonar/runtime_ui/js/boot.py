#!/usr/bin/env python3
from __future__ import annotations

JS = r"""document.getElementById("cards").addEventListener("click", event => {
  if(event.target.closest(INTERACTIVE_SELECTOR) || event.target.closest("[data-external-url]")) return;
  const card = event.target.closest("[data-select-url]");
  if(!card) return;
  toggleSelected(card.getAttribute("data-select-url"));
});

document.getElementById("cards").addEventListener("keydown", event => {
  if(event.ctrlKey || event.metaKey || event.altKey) return;
  const card = event.target.closest("[data-select-url]");
  if(!card) return;

  if((event.key === "Enter" || event.key === " ") && !event.target.closest(INTERACTIVE_SELECTOR) && !event.target.closest("[data-external-url]")){
    event.preventDefault();
    toggleSelected(card.getAttribute("data-select-url"));
    return;
  }

  if(["ArrowDown", "ArrowUp", "ArrowLeft", "ArrowRight"].includes(event.key)) {
    event.preventDefault();
    const cards = Array.from(document.querySelectorAll("#cards .selectable"));
    const idx = cards.indexOf(card);
    if((event.key === "ArrowDown" || event.key === "ArrowRight") && idx < cards.length - 1) cards[idx + 1].focus();
    if((event.key === "ArrowUp" || event.key === "ArrowLeft") && idx > 0) cards[idx - 1].focus();
    return;
  }

  if(event.shiftKey && event.key >= "1" && event.key <= "4") {
    event.preventDefault();
    const states = ["favorites", "watch_later", "read", "ignored"];
    batchSetState(states[parseInt(event.key) - 1]);
    return;
  }
});

document.getElementById("search").value = localStorage.getItem("gtr-search") || "";
let __searchDebounceTimer;
document.getElementById("search").addEventListener("input", event => {
  localStorage.setItem("gtr-search", event.target.value);
  clearTimeout(__searchDebounceTimer);
  __searchDebounceTimer = setTimeout(() => { render(); }, 200);
});

document.getElementById("import-user-state-input").addEventListener("change", event => {
  const file = event.target.files?.[0];
  if(file) importUserStateFile(file);
});

document.getElementById("language").addEventListener("change", event => {
  languageFilter = event.target.value;
  localStorage.setItem("gtr-language", languageFilter);
  render();
});

document.getElementById("workspace-back-to-top")?.addEventListener("click", () => {
  scrollWorkspaceToTop();
});

document.querySelectorAll("#discover-query").forEach(node => {
  node.addEventListener("focus", () => {
    openDiscoverySuggestions();
  });
  node.addEventListener("input", event => {
    discoverDraft.viewId = "";
    discoverDraft.limit = currentDiscoveryLimit();
    discoverDraft.query = event.target.value;
    openDiscoverySuggestions();
    syncDiscoverDraftUI();
  });
  node.addEventListener("blur", () => {
    scheduleCloseDiscoverySuggestions();
  });
  node.addEventListener("keydown", event => {
    if(event.key === "Escape"){
      closeDiscoverySuggestions();
      return;
    }
    if(event.key !== "Enter" || event.shiftKey || event.altKey || event.ctrlKey || event.metaKey) return;
    event.preventDefault();
    closeDiscoverySuggestions();
    runDiscovery();
  });
});

document.getElementById("discover-auto-expand").addEventListener("change", event => {
  discoverDraft.viewId = "";
  discoverDraft.limit = currentDiscoveryLimit();
  discoverDraft.autoExpand = !!event.target.checked;
  syncDiscoverDraftUI();
});


document.getElementById("setting-token").addEventListener("input", () => {
  document.getElementById("setting-clear-token").checked = false;
  syncSensitiveSettingHints();
  applyTokenStatus({
    state:"idle",
    message:"输入已变更，离开输入框后会重新校验 GitHub Token。",
  });
});

document.getElementById("setting-token").addEventListener("blur", () => {
  validateTokenStatus();
});

document.getElementById("setting-clear-token").addEventListener("change", event => {
  if(event.target.checked){
    document.getElementById("setting-token").value = "";
  }
  syncSensitiveSettingHints();
  validateTokenStatus();
});

document.getElementById("setting-proxy").addEventListener("input", () => {
  document.getElementById("setting-clear-proxy").checked = false;
  syncSensitiveSettingHints();
});

document.getElementById("setting-clear-proxy").addEventListener("change", event => {
  if(event.target.checked){
    document.getElementById("setting-proxy").value = "";
  }
  syncSensitiveSettingHints();
});

document.getElementById("setting-translation-api-key").addEventListener("input", () => {
  document.getElementById("setting-clear-translation-api-key").checked = false;
  syncSensitiveSettingHints();
});

document.getElementById("setting-clear-translation-api-key").addEventListener("change", event => {
  if(event.target.checked){
    document.getElementById("setting-translation-api-key").value = "";
  }
  syncSensitiveSettingHints();
});

document.querySelectorAll("#state-filter-seg [data-value]").forEach(btn => {
  btn.addEventListener("click", () => {
    if(btn.disabled) return;
    setStateFilter(btn.dataset.value || "");
  });
});

document.querySelectorAll("#sort-primary-seg [data-sort-primary]").forEach(btn => {
  btn.addEventListener("click", () => {
    if(btn.disabled) return;
    setSortPrimary(btn.dataset.sortPrimary);
  });
});

document.getElementById("settings-modal").addEventListener("click", event => {
  if(event.target.id === "settings-modal") closeSettings();
});
document.getElementById("detail-modal").addEventListener("click", event => {
  if(event.target.id === "detail-modal") closeDetail();
});
document.getElementById("compare-modal").addEventListener("click", event => {
  if(event.target.id === "compare-modal") closeCompare();
});
document.getElementById("diagnostics-modal").addEventListener("click", event => {
  if(event.target.id === "diagnostics-modal") closeDiagnostics();
});

document.addEventListener("click", event => {
  const externalTarget = event.target.closest("[data-external-url]");
  if(externalTarget){
    event.preventDefault();
    event.stopPropagation();
    openExternalUrl(externalTarget.getAttribute("data-external-url"));
    return;
  }
  if(!event.target.closest("[data-menu-id]")) closeMenus();
  if(!event.target.closest(".discover-query-field")) closeDiscoverySuggestions();
});

window.addEventListener("resize", () => {
  repositionOpenMenus();
  queueExpandableDescriptionsSync(document, {force:true});
  queueBackToTopButtonSync();
});

window.addEventListener("scroll", () => {
  queueBackToTopButtonSync();
}, {passive:true});

document.addEventListener("scroll", event => {
  if(shouldSkipMenuScrollReposition(event.target)) return;
  repositionOpenMenus();
}, true);

window.addEventListener("keydown", event => {
  if(event.key !== "Escape") return;
  closeDiscoverySuggestions();
  closeMenus();
  closeControlDrawer();
  closeSettings();
  closeDetail();
  closeCompare();
  closeDiagnostics();
});

async function resumeDiscoveryRuntime(){
  try{
    const {resp, data} = await requestJson("/api/discovery", {cache:"no-store"}, "读取关键词发现状态失败");
    if(!resp.ok || !data.ok) return;
    discoveryState = data.discovery_state || discoveryState;
    const job = data.active_job || null;
    if(job?.id){
      applyActiveDiscoveryJob(job);
      render();
      if(!isTerminalDiscoveryJob(job)) startDiscoveryPolling(job.id);
      return;
    }
    activeDiscoveryJob = null;
    discoveryBusy = false;
    discoveryStartedAt = 0;
    render();
  }catch(_error){}
}

render();
resumeDiscoveryRuntime();
if(INITIAL.pending) poll();"""
