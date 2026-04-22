#!/usr/bin/env python3
from __future__ import annotations

JS = r"""const MENU_HOST_SELECTOR = ".workspace-header,.workspace-nav-shell,.workspace-content-shell,.workspace-control-stack,.workspace-drawer,.card,.update-card,.panel,.batch-dock,.canvas-intro";
const MENU_VIEWPORT_MARGIN = 12;
const MENU_PANEL_GAP = 10;
let menuRepositionFrame = 0;

function menuRoot(id){
  return document.querySelector(`[data-menu-id="${id}"]`);
}

function menuPanel(root){
  return root?.querySelector(".menu-panel") || null;
}

function customSelectRoot(selectId){
  return document.querySelector(`[data-custom-select-for="${selectId}"]`);
}

function customSelectOptionDescription(selectId, value){
  if(selectId === "discover-ranking-profile") return discoveryRankingDescription(value);
  return "";
}

function rememberMenuPanelDefaults(panel){
  if(!panel) return;
  if(!panel.dataset.defaultAlign){
    panel.dataset.defaultAlign = panel.classList.contains("align-left") ? "left" : "right";
  }
  if(!panel.dataset.defaultUpward){
    panel.dataset.defaultUpward = panel.classList.contains("upward") ? "true" : "false";
  }
}

function resetMenuPanelPosition(root){
  const panel = menuPanel(root);
  if(!panel) return;
  rememberMenuPanelDefaults(panel);
  panel.classList.toggle("align-left", panel.dataset.defaultAlign === "left");
  panel.classList.toggle("align-right", panel.dataset.defaultAlign === "right");
  panel.classList.toggle("upward", panel.dataset.defaultUpward === "true");
  panel.style.left = "";
  panel.style.right = "";
  panel.style.maxHeight = "";
  panel.style.overflowY = "";
}

function withMeasuredMenuPanel(root, callback){
  const panel = menuPanel(root);
  if(!root || !panel) return null;
  panel.classList.add("menu-panel--measuring");
  try{
    return callback(panel);
  } finally {
    panel.classList.remove("menu-panel--measuring");
  }
}

function syncMenuRootState(root){
  if(!root) return;
  const expanded = root.classList.contains("open");
  root.querySelectorAll("[aria-haspopup]").forEach(node => {
    node.setAttribute("aria-expanded", expanded ? "true" : "false");
  });
  const host = root.closest(MENU_HOST_SELECTOR);
  if(host) host.classList.toggle("menu-host-open", expanded);
  if(!expanded) resetMenuPanelPosition(root);
}

function positionMenu(root){
  withMeasuredMenuPanel(root, panel => {
    resetMenuPanelPosition(root);

    const rootRect = root.getBoundingClientRect();
    const naturalHeight = panel.scrollHeight;
    const viewportHeight = Math.max(0, window.innerHeight - MENU_VIEWPORT_MARGIN * 2);
    const spaceBelow = Math.max(0, window.innerHeight - rootRect.bottom - MENU_VIEWPORT_MARGIN - MENU_PANEL_GAP);
    const spaceAbove = Math.max(0, rootRect.top - MENU_VIEWPORT_MARGIN - MENU_PANEL_GAP);
    const minUsableHeight = Math.min(naturalHeight, 160);
    let openUpward = panel.dataset.defaultUpward === "true";
    if(!openUpward && spaceBelow < minUsableHeight && spaceAbove > spaceBelow){
      openUpward = true;
    }else if(openUpward && spaceAbove < minUsableHeight && spaceBelow > spaceAbove){
      openUpward = false;
    }
    panel.classList.toggle("upward", openUpward);

    const availableHeight = Math.max(0, openUpward ? spaceAbove : spaceBelow);
    const fallbackHeight = Math.max(spaceAbove, spaceBelow);
    const fittedHeight = Math.floor(Math.min(naturalHeight, viewportHeight, availableHeight || fallbackHeight));
    if(fittedHeight > 0){
      panel.style.maxHeight = `${fittedHeight}px`;
      panel.style.overflowY = naturalHeight > fittedHeight ? "auto" : "";
    }

    let panelRect = panel.getBoundingClientRect();

    const fitsLeft = rootRect.left + panelRect.width <= window.innerWidth - MENU_VIEWPORT_MARGIN;
    const fitsRight = rootRect.right - panelRect.width >= MENU_VIEWPORT_MARGIN;
    if(panelRect.right > window.innerWidth - MENU_VIEWPORT_MARGIN){
      if(fitsRight){
        panel.classList.remove("align-left");
        panel.classList.add("align-right");
        panel.style.left = "";
        panel.style.right = "0px";
      } else if(fitsLeft){
        panel.classList.remove("align-right");
        panel.classList.add("align-left");
        panel.style.left = "0px";
        panel.style.right = "auto";
      }
      panelRect = panel.getBoundingClientRect();
    } else if(panelRect.left < MENU_VIEWPORT_MARGIN){
      if(fitsLeft){
        panel.classList.remove("align-right");
        panel.classList.add("align-left");
        panel.style.left = "0px";
        panel.style.right = "auto";
      } else if(fitsRight){
        panel.classList.remove("align-left");
        panel.classList.add("align-right");
        panel.style.left = "";
        panel.style.right = "0px";
      }
      panelRect = panel.getBoundingClientRect();
    }

    if(panelRect.right > window.innerWidth - MENU_VIEWPORT_MARGIN || panelRect.left < MENU_VIEWPORT_MARGIN){
      const currentLeft = panel.classList.contains("align-left") ? 0 : (rootRect.width - panelRect.width);
      const minLeft = MENU_VIEWPORT_MARGIN - rootRect.left;
      const maxLeft = window.innerWidth - MENU_VIEWPORT_MARGIN - rootRect.left - panelRect.width;
      const clampedLeft = Math.min(Math.max(currentLeft, minLeft), maxLeft);
      panel.style.left = `${Math.round(clampedLeft)}px`;
      panel.style.right = "auto";
    }
  });
}

function positionOpenMenusNow(){
  document.querySelectorAll("[data-menu-id].open").forEach(positionMenu);
}

function repositionOpenMenus(){
  if(menuRepositionFrame) return;
  menuRepositionFrame = requestAnimationFrame(() => {
    menuRepositionFrame = 0;
    positionOpenMenusNow();
  });
}

function shouldSkipMenuScrollReposition(target){
  return target instanceof Element && !!target.closest(".menu-panel,.select-menu");
}

function closeMenus(exceptId = ""){
  document.querySelectorAll("[data-menu-id].open").forEach(root => {
    if(root.dataset.menuId !== exceptId) root.classList.remove("open");
    syncMenuRootState(root);
  });
}

function toggleMenu(event, id){
  if(event){
    event.preventDefault();
    event.stopPropagation();
    if(event.currentTarget?.disabled) return;
  }
  const root = menuRoot(id);
  if(!root) return;
  const willOpen = !root.classList.contains("open");
  closeMenus(willOpen ? id : "");
  if(willOpen) positionMenu(root);
  root.classList.toggle("open", willOpen);
  syncMenuRootState(root);
}

function syncCustomSelect(selectId){
  const select = document.getElementById(selectId);
  const root = customSelectRoot(selectId);
  if(!select || !root) return;
  const trigger = root.querySelector(".select-trigger");
  const textNode = root.querySelector(".select-trigger-text");
  const panel = root.querySelector(".select-menu");
  if(!trigger || !textNode || !panel) return;

  const options = [...select.options];
  const firstEnabled = options.find(option => !option.disabled) || options[0] || null;
  if(!options.some(option => option.value === select.value) && firstEnabled){
    select.value = firstEnabled.value;
  }
  const currentValue = String(select.value ?? "");
  const currentOption = options.find(option => option.value === currentValue) || firstEnabled;

  textNode.textContent = String(currentOption?.textContent || "").trim();
  trigger.disabled = !!select.disabled;
  if(select.disabled){
    root.classList.remove("open");
    syncMenuRootState(root);
  }

  panel.innerHTML = options.map(option => {
    const value = String(option.value ?? "");
    const label = String(option.textContent || "").trim() || value;
    const description = customSelectOptionDescription(selectId, value);
    const activeClass = value === currentValue ? " active" : "";
    const disabledAttr = option.disabled ? " disabled" : "";
    const selectedAttr = value === currentValue ? "true" : "false";
    return `<button class="menu-item${activeClass}" type="button" role="option" aria-selected="${selectedAttr}"${disabledAttr} onclick='setCustomSelectValue(${JSON.stringify(selectId)}, ${JSON.stringify(value)})'>
      <span class="menu-item-copy">
        <span>${h(label)}</span>
        ${description ? `<span class="menu-item-meta">${h(description)}</span>` : ""}
      </span>
    </button>`;
  }).join("");

  syncMenuRootState(root);
}

function syncAllCustomSelects(){
  document.querySelectorAll("[data-custom-select-for]").forEach(root => {
    syncCustomSelect(root.dataset.customSelectFor || "");
  });
}

function setCustomSelectValue(selectId, value){
  const select = document.getElementById(selectId);
  if(!select || select.disabled) return;
  const nextValue = String(value ?? "");
  select.value = nextValue;
  if(select.value !== nextValue){
    const firstEnabled = [...select.options].find(option => !option.disabled);
    if(firstEnabled) select.value = firstEnabled.value;
  }
  select.dispatchEvent(new Event("change", {bubbles:true}));
  syncCustomSelect(selectId);
  closeMenus();
}

function setStateFilter(value){
  stateFilter = normalizeStateFilter(value);
  localStorage.setItem("gtr-state-filter", stateFilter);
  render();
}

function setSortPrimary(value){
  sortPrimary = normalizeSortKey(value);
  localStorage.setItem("gtr-sort-primary", sortPrimary);
  closeMenus();
  render();
}

function toggleAiTarget(value){
  if(!VALID_AI_TARGETS.has(value)) return;
  if(value === "copy"){
    aiTargets = new Set(["copy"]);
  } else {
    aiTargets.delete("copy");
    if(aiTargets.has(value)){
      if(aiTargets.size > 1) aiTargets.delete(value);
    } else {
      aiTargets.add(value);
    }
  }
  localStorage.setItem("gtr-ai-targets", JSON.stringify([...aiTargets]));
  closeMenus();
  syncAiTargetUI();
}

function syncStateFilterUI(){
  document.querySelectorAll("#state-filter-seg [data-value]").forEach(btn => {
    btn.classList.toggle("active", (btn.dataset.value || "") === stateFilter);
  });
}

function syncSortUI(){
  document.querySelectorAll("#sort-primary-seg [data-sort-primary]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.sortPrimary === sortPrimary);
  });
  const isMoreSort = !PRIMARY_SORT_KEYS.includes(sortPrimary);
  const moreToggle = document.getElementById("sort-more-toggle");
  moreToggle.classList.toggle("is-subactive", isMoreSort);
  document.getElementById("sort-more-current").textContent = isMoreSort ? `· ${SORT_LABELS[sortPrimary] || ""}` : "";
  document.querySelectorAll("[data-sort-more]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.sortMore === sortPrimary);
  });
}

function syncAiTargetUI(){
  const label = currentDiscoveryAiTargetLabel();
  document.querySelectorAll("[data-ai-target-label]").forEach(node => {
    node.textContent = label;
  });
  document.querySelectorAll("[data-ai-target]").forEach(btn => {
    btn.classList.toggle("active", aiTargets.has(btn.dataset.aiTarget));
  });
}"""
