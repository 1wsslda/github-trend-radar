#!/usr/bin/env python3
from __future__ import annotations

JS = r"""const INITIAL = __PAYLOAD__;
const DISCOVER_PANEL_KEY = "discover";
const UPDATE_PANEL_KEY = "favorite-updates";
const OVERLAY_IDS = ["settings-modal", "detail-modal", "compare-modal"];
const INTERACTIVE_SELECTOR = "button,a,input,select,label,textarea";
const SORT_KEYS = new Set(["stars","trending","gained","forks","name","language"]);
const PRIMARY_SORT_KEYS = ["stars","trending","gained"];
const STATE_FILTER_KEYS = new Set(["","unmarked","favorites","watch_later","read","ignored"]);
const PRIMARY_STATE_KEYS = new Set(["favorites","watch_later"]);
const LEGACY_STATE_PANEL_KEYS = new Set(["favorites","watch_later","read","ignored"]);
const SORT_LABELS = {
  stars:"总星标",
  trending:"趋势",
  gained:"增长",
  forks:"Fork",
  name:"仓库名",
  language:"语言",
};
const AI_TARGET_LABELS = {
  web:"ChatGPT 网页版",
  desktop:"ChatGPT 桌面版",
  gemini_web:"Gemini 网页版",
  copy:"仅复制提示词",
};
const VALID_AI_TARGETS = new Set(["web","desktop","gemini_web","copy"]);
const DISCOVERY_RANKING_LABELS = {
  balanced:"综合排序",
  hot:"热门优先",
  fresh:"新项目优先",
  builder:"实用优先",
  trend:"趋势优先",
};
const DISCOVERY_RANKING_DESCRIPTIONS = {
  balanced:"平衡相关性、热度与可用性，适合先看全局。",
  hot:"更偏向社区热度高、讨论更多的项目。",
  fresh:"更偏向较新、近期冒头的新项目。",
  builder:"更偏向信息完整、工程上更容易落地的项目。",
  trend:"更偏向近期增速快、话题正在上升的项目。",
};
let snapshot = INITIAL.snapshot || {};
let userState = INITIAL.userState || {};
let discoveryState = INITIAL.discoveryState || {};
let settings = INITIAL.settings || {};
let currentNote = INITIAL.note || "";
let panel = normalizePanelKey(localStorage.getItem("gtr-tab") || "daily");
let stateFilter = normalizeStateFilter(localStorage.getItem("gtr-state-filter") || "");
let sortPrimary = normalizeSortKey(localStorage.getItem("gtr-sort-primary") || settings.default_sort || "stars");
let aiTargets = normalizeAiTargets(localStorage.getItem("gtr-ai-targets") || localStorage.getItem("gtr-ai-target") || "");
let comparePrompt = "";
let selectedUrls = loadSelectedUrls();
let languageFilter = localStorage.getItem("gtr-language") || "";
let discoverDraft = loadDiscoverDraft();
let pendingImportMode = "merge";
let discoveryBusy = false;
let discoveryStartedAt = 0;
let activeDiscoveryJob = null;
let discoveryPollToken = 0;

normalizeRuntimePayload();

function normalizeSortKey(value){
  const key = String(value || "").trim();
  return SORT_KEYS.has(key) ? key : "stars";
}

function normalizeStateFilter(value){
  const key = String(value || "").trim();
  return STATE_FILTER_KEYS.has(key) ? key : "";
}

function normalizeAiTargets(raw){
  try{
    const parsed = JSON.parse(raw || "");
    if(Array.isArray(parsed)){
      const valid = parsed.filter(v => VALID_AI_TARGETS.has(String(v)));
      if(valid.length) return new Set(valid);
    }
  }catch(_){}
  // 兼容旧版单值格式
  const single = String(raw || "").trim();
  return VALID_AI_TARGETS.has(single) ? new Set([single]) : new Set(["web"]);
}

function normalizeDiscoveryRankingProfile(value){
  const key = String(value || "").trim();
  return Object.prototype.hasOwnProperty.call(DISCOVERY_RANKING_LABELS, key) ? key : "balanced";
}

function discoveryRankingLabel(value){
  const key = normalizeDiscoveryRankingProfile(value);
  return DISCOVERY_RANKING_LABELS[key] || DISCOVERY_RANKING_LABELS.balanced;
}

function discoveryRankingDescription(value){
  const key = normalizeDiscoveryRankingProfile(value);
  return DISCOVERY_RANKING_DESCRIPTIONS[key] || DISCOVERY_RANKING_DESCRIPTIONS.balanced;
}

function normalizePanelKey(value){
  const key = String(value || "").trim();
  if(!key) return "daily";
  if(key === "updates") return UPDATE_PANEL_KEY;
  if(LEGACY_STATE_PANEL_KEYS.has(key)) return `saved:${key}`;
  return key;
}

function normalizeUpdateEntry(payload){
  const raw = payload && typeof payload === "object" ? payload : {};
  const repo = raw.repo && typeof raw.repo === "object" ? raw.repo : {};
  const previous = raw.old_repo_state && typeof raw.old_repo_state === "object" ? raw.old_repo_state : {};
  const url = String(raw.url || repo.url || "").trim();
  const fullName = String(raw.full_name || repo.full_name || "").trim();
  if(!url || !fullName) return null;

  const changes = [];
  if(Array.isArray(raw.changes)){
    raw.changes.forEach(item => {
      const change = String(item || "").trim();
      if(change) changes.push(change);
    });
  }
  if(!changes.length && Number.isFinite(Number(previous.stars)) && Number(repo.stars || raw.stars || 0) !== Number(previous.stars || 0)){
    changes.push(`Star ${Number(previous.stars || 0)} → ${Number(repo.stars || raw.stars || 0)}`);
  }
  if(!changes.length && Number.isFinite(Number(previous.forks)) && Number(repo.forks || raw.forks || 0) !== Number(previous.forks || 0)){
    changes.push(`Fork ${Number(previous.forks || 0)} → ${Number(repo.forks || raw.forks || 0)}`);
  }
  const summary = String(raw.change_summary || "").trim();
  if(summary) changes.push(summary);
  if(!changes.length && String(repo.latest_release_tag || raw.latest_release_tag || "").trim()){
    changes.push(`新版本 ${String(repo.latest_release_tag || raw.latest_release_tag).trim()}`);
  }
  if(!changes.length && String(repo.pushed_at || raw.pushed_at || "").trim()){
    changes.push("仓库有新的提交活动");
  }
  if(!changes.length){
    changes.push("检测到仓库更新");
  }

  const checkedAt = String(raw.checked_at || "").trim();
  const timestamp = Number(raw.timestamp || 0);
  const fallbackCheckedAt = checkedAt || (timestamp > 0 ? new Date(timestamp * 1000).toLocaleString("zh-CN", {hour12:false}) : "");

  return {
    id:String(raw.id || `${fullName}:${fallbackCheckedAt || url}`),
    full_name:fullName,
    url,
    checked_at:fallbackCheckedAt,
    changes,
    stars:Number(raw.stars || repo.stars || 0) || 0,
    forks:Number(raw.forks || repo.forks || 0) || 0,
    latest_release_tag:String(raw.latest_release_tag || repo.latest_release_tag || "").trim(),
    pushed_at:String(raw.pushed_at || repo.pushed_at || "").trim(),
  };
}

function normalizeRuntimePayload(){
  if(!snapshot || typeof snapshot !== "object") snapshot = {};
  if(!userState || typeof userState !== "object") userState = {};
  if(!userState.repo_records || typeof userState.repo_records !== "object") userState.repo_records = {};
  if(!Array.isArray(userState.favorite_updates)) userState.favorite_updates = [];

  if(Array.isArray(snapshot.periods)){
    snapshot.periods.forEach(period => {
      if(!period || typeof period !== "object") return;
      const key = String(period.key || "").trim();
      if(!key || Array.isArray(snapshot[key]) || !Array.isArray(period.items)) return;
      snapshot[key] = period.items;
    });
  }

  const normalizedUpdates = [];
  const seenUpdateIds = new Set();
  [...(userState.favorite_updates || []), ...(Array.isArray(snapshot.favorite_updates) ? snapshot.favorite_updates : [])].forEach(entry => {
    const clean = normalizeUpdateEntry(entry);
    if(!clean || seenUpdateIds.has(clean.id)) return;
    normalizedUpdates.push(clean);
    seenUpdateIds.add(clean.id);
  });
  userState.favorite_updates = normalizedUpdates;
}

function periodDefs(){
  if(Array.isArray(INITIAL.periods) && INITIAL.periods.length) return INITIAL.periods;
  if(Array.isArray(snapshot.periods) && snapshot.periods.length) return snapshot.periods;
  return [
    {key:"daily", label:"今天"},
    {key:"weekly", label:"本周"},
    {key:"monthly", label:"本月"},
  ].filter(period => Array.isArray(snapshot[period.key]));
}

function stateDefs(){
  if(Array.isArray(INITIAL.states) && INITIAL.states.length) return INITIAL.states;
  return [
    {key:"favorites", label:"关注"},
    {key:"watch_later", label:"待看"},
    {key:"read", label:"已读"},
    {key:"ignored", label:"忽略"},
  ];
}

function loadSelectedUrls(){
  try{
    const raw = JSON.parse(localStorage.getItem("gtr-selected") || "[]");
    return new Set(Array.isArray(raw) ? raw.filter(Boolean) : []);
  }catch(_err){
    return new Set();
  }
}

function saveSelectedUrls(){
  localStorage.setItem("gtr-selected", JSON.stringify([...selectedUrls]));
}

function loadDiscoverDraft(){
  const lastQuery = INITIAL.discoveryState?.last_query || {};
  const limit = Number(localStorage.getItem("gtr-discover-limit") || lastQuery.limit || settings.result_limit || 20);
  return {
    query:localStorage.getItem("gtr-discover-query") || lastQuery.query || "",
    language:localStorage.getItem("gtr-discover-language") || lastQuery.language || "",
    limit:Number.isFinite(limit) ? Math.max(5, Math.min(50, limit)) : 20,
    autoExpand:(localStorage.getItem("gtr-discover-auto-expand") ?? String(lastQuery.auto_expand ?? true)) !== "false",
    rankingProfile:normalizeDiscoveryRankingProfile(localStorage.getItem("gtr-discover-ranking-profile") || lastQuery.ranking_profile || "balanced"),
    saveQuery:localStorage.getItem("gtr-discover-save-query") === "true",
  };
}

function saveDiscoverDraft(){
  localStorage.setItem("gtr-discover-query", discoverDraft.query || "");
  localStorage.setItem("gtr-discover-language", discoverDraft.language || "");
  localStorage.setItem("gtr-discover-limit", String(discoverDraft.limit || 20));
  localStorage.setItem("gtr-discover-auto-expand", discoverDraft.autoExpand ? "true" : "false");
  localStorage.setItem("gtr-discover-ranking-profile", normalizeDiscoveryRankingProfile(discoverDraft.rankingProfile));
  localStorage.setItem("gtr-discover-save-query", discoverDraft.saveQuery ? "true" : "false");
}"""
