#!/usr/bin/env python3
from __future__ import annotations

JS = r"""const INITIAL = __PAYLOAD__;
const DISCOVER_PANEL_KEY = "discover";
const UPDATE_PANEL_KEY = "favorite-updates";
const FILTER_PANEL_STORAGE_KEY = "gtr-filter-panel";
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
  balanced:"综合平衡",
  hot:"偏热门",
  fresh:"偏新项目",
  builder:"偏工程可用",
  trend:"偏趋势",
};
const CUSTOM_SELECT_IDS = ["language","discover-ranking-profile"];

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
let filterPanelOpen = (localStorage.getItem(FILTER_PANEL_STORAGE_KEY) ?? "true") === "true";
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
}

function h(value){
  return String(value ?? "").replace(/[&<>"']/g, char => {
    if(char === "&") return "&amp;";
    if(char === "<") return "&lt;";
    if(char === ">") return "&gt;";
    if(char === '"') return "&quot;";
    return "&#39;";
  });
}

function sleep(ms){
  return new Promise(resolve => setTimeout(resolve, ms));
}

function toast(message){
  const text = String(message || "").trim();
  if(!text) return;
  const node = document.getElementById("toast");
  node.textContent = text;
  node.classList.add("show");
  clearTimeout(window.__toastTimer);
  const duration = Math.min(5200, Math.max(2400, text.length * 70));
  window.__toastTimer = setTimeout(() => node.classList.remove("show"), duration);
}

async function copyText(text, label){
  const value = String(text || "").trim();
  if(!value){
    toast("没有可复制的内容");
    return false;
  }
  try{
    if(navigator.clipboard && navigator.clipboard.writeText){
      await navigator.clipboard.writeText(value);
    }else{
      throw new Error("clipboard");
    }
  }catch(_err){
    const area = document.createElement("textarea");
    area.value = value;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.focus();
    area.select();
    document.execCommand("copy");
    document.body.removeChild(area);
  }
  toast(label || "已复制");
  return true;
}

async function requestJson(url, options, errorMessage = "无法连接本地服务"){
  let resp;
  try{
    resp = await fetch(url, options);
  }catch(_err){
    throw new Error(errorMessage);
  }
  const rawText = await resp.text();
  let data = {};
  if(rawText){
    try{
      data = JSON.parse(rawText);
    }catch(_err){
      throw new Error(resp.ok ? "服务返回了无效数据" : errorMessage);
    }
  }
  return {resp, data};
}

function isTerminalDiscoveryJob(job){
  return ["completed","failed","cancelled"].includes(String(job?.status || "").trim());
}

function applyActiveDiscoveryJob(job){
  activeDiscoveryJob = job && job.id ? job : null;
  discoveryBusy = !!(activeDiscoveryJob && !isTerminalDiscoveryJob(activeDiscoveryJob));
  if(activeDiscoveryJob){
    const elapsed = Number(activeDiscoveryJob.elapsed_seconds || 0);
    discoveryStartedAt = Date.now() - (Number.isFinite(elapsed) ? elapsed * 1000 : 0);
  }else{
    discoveryStartedAt = 0;
  }
}

function current(key){
  return Array.isArray(snapshot[key]) ? snapshot[key] : [];
}

function saved(key){
  return (userState[key] || []).map(url => userState.repo_records?.[url] || repoByUrl(url) || synthesizeRepoFromUrl(url)).filter(Boolean);
}

function discoveryResults(){
  if(activeDiscoveryJob && activeDiscoveryJob.status !== "completed" && Array.isArray(activeDiscoveryJob.preview_results) && activeDiscoveryJob.preview_results.length){
    return activeDiscoveryJob.preview_results;
  }
  return Array.isArray(discoveryState.last_results) ? discoveryState.last_results : [];
}

function savedDiscoveryQueries(){
  return Array.isArray(discoveryState.saved_queries) ? discoveryState.saved_queries : [];
}

function updateByUrl(url){
  return (userState.favorite_updates || []).find(item => item.url === url) || null;
}

function synthesizeRepoFromUpdate(update){
  if(!update || !String(update.full_name || "").includes("/")) return null;
  const [owner, name] = String(update.full_name).split("/", 2);
  return {
    full_name:update.full_name,
    owner,
    name,
    url:update.url,
    description:"",
    description_raw:"",
    language:"",
    stars:update.stars || 0,
    forks:update.forks || 0,
    gained:0,
    gained_text:"",
    growth_source:"unavailable",
    rank:0,
    period_key:UPDATE_PANEL_KEY,
    source_label:"收藏更新",
  };
}

function synthesizeRepoFromUrl(url){
  const link = String(url || "").trim();
  if(!link) return null;
  try{
    const parts = new URL(link).pathname.split("/").filter(Boolean);
    if(parts.length < 2) return null;
    const [owner, name] = parts;
    return {
      full_name:`${owner}/${name}`,
      owner,
      name,
      url:link,
      description:"当前快照里没有这条仓库记录。",
      description_raw:"当前快照里没有这条仓库记录。",
      language:"",
      stars:0,
      forks:0,
      gained:0,
      gained_text:"",
      growth_source:"unavailable",
      rank:0,
      period_key:"saved",
      source_label:"本地状态",
    };
  }catch(_err){
    return null;
  }
}

function repoByUrl(url){
  for(const period of periodDefs()){
    const hit = current(period.key).find(repo => repo.url === url);
    if(hit) return hit;
  }
  const discoveryHit = discoveryResults().find(repo => repo.url === url);
  if(discoveryHit) return discoveryHit;
  if(userState.repo_records?.[url]) return userState.repo_records[url];
  return synthesizeRepoFromUpdate(updateByUrl(url)) || synthesizeRepoFromUrl(url);
}

function panelRepoSource(){
  if(panel === UPDATE_PANEL_KEY) return [];
  if(panel === DISCOVER_PANEL_KEY) return discoveryResults();
  return panel.startsWith("saved:") ? saved(panel.split(":")[1]) : current(panel);
}

function cleanupSelected(){
  const valid = [...selectedUrls].filter(url => repoByUrl(url) || updateByUrl(url));
  if(valid.length !== selectedUrls.size){
    selectedUrls = new Set(valid);
    saveSelectedUrls();
  }
}

function selectedRepos(){
  cleanupSelected();
  const seen = new Set();
  return [...selectedUrls]
    .map(url => repoByUrl(url))
    .filter(repo => repo && !seen.has(repo.url) && seen.add(repo.url));
}

function selectedCount(){
  cleanupSelected();
  return selectedUrls.size;
}

function growthSource(repo){
  return String(repo?.growth_source || "").trim();
}

function hasGrowthValue(repo){
  return Number(repo?.gained || 0) > 0 || growthSource(repo) === "trending";
}

function gainBadgeClass(repo){
  return hasGrowthValue(repo) ? "gain" : "source";
}

function gainLabel(repo){
  const source = growthSource(repo);
  if(source === "estimated"){
    return Number(repo?.gained || 0) > 0 ? `较上次 +${repo.gained}` : "较上次持平";
  }
  if(source === "unavailable"){
    if(String(repo?.source_label || "").includes("收藏更新")) return "更新追踪项";
    return "待下次估算";
  }
  if(repo.gained_text) return repo.gained_text;
  if((repo.gained || 0) > 0) return `+${repo.gained}`;
  return "暂无增长数据";
}

function repoLine(repo){
  return `- ${repo.full_name} | ${repo.language || "未知语言"} | Stars ${repo.stars || 0} | ${repo.url}\n  简介: ${repo.description || repo.description_raw || "暂无描述"}`;
}

function buildRepoPrompt(repo){
  return `你是一位资深技术总监兼产品战略专家。请阅读下方仓库信息，用中文输出一份简洁的研判报告。
语言要求：直白通俗，遇到复杂技术概念用生活例子打比方；禁止堆砌术语和官方套话。

【仓库信息】
名称：${repo.full_name}
链接：${repo.url}
语言：${repo.language || "未知语言"}
总星标：${repo.stars || 0}
增长：${gainLabel(repo)}
来源：${repo.source_label || "未知来源"}
简介：${repo.description || repo.description_raw || "暂无描述"}

【输出结构】
1. 🎯 一句话大白话解释
（向不懂技术的人解释，这东西是干嘛的？）

2. 💡 核心价值（2-3 条）
（用它能省什么事、解决什么恶心问题？）

3. ⚠️ 坑和局限（不要客气）
（学习成本、适用范围、维护状态、常见踩坑点）

4. 🛠️ 一个具体使用场景
（假设你正在做某个真实项目，遇到 XX 问题，你会怎么用它？）

5. 🔍 主流竞品对比
（同类工具有哪些？它和主流方案最大的差异点是什么？）

6. ⚖️ 决策建议
（直接给结论：立刻试用 / 持续观望 / 特定场景再看。一句话说明理由。）`;
}

function buildBatchPrompt(repos, title, batchIndex, batchCount){
  const groupNote = batchCount > 1 ? `\n（当前是第 ${batchIndex}/${batchCount} 组）` : "";
  return `你是一位资深架构师，正在帮团队快速筛选值得关注的开源项目。
请用中文对下方每个仓库分别输出简洁研判，语言直白、不堆砌术语。${groupNote}

分析范围：${title}

仓库列表：
${repos.map(repoLine).join("\n")}

【每个仓库输出以下 4 项，用仓库名作为小标题】
1. 一句话说清楚它是干嘛的（大白话）
2. 最大的实际价值或亮点（1-2 条，具体场景）
3. 主要风险或局限（不要客气）
4. 决策建议：立刻试用 / 持续观望 / 暂时忽略（一句理由）`;
}

function splitRepoPrompts(repos, title, maxEncodedLength = 2600, maxItemsPerBatch = 4){
  const normalized = repos.filter(Boolean);
  if(!normalized.length) return [];
  if(normalized.length === 1) return [buildRepoPrompt(normalized[0])];
  const batches = [];
  let currentBatch = [];
  const buildDraft = candidate => `你是一位资深架构师，正在帮团队快速筛选值得关注的开源项目。请用中文对下方每个仓库分别输出简洁研判。\n分析范围：${title}\n仓库列表：\n${candidate.map(repoLine).join("\n")}\n【每个仓库输出：1.一句话说清楚 2.最大价值亮点 3.主要风险 4.决策建议】`;
  for(const repo of normalized){
    const candidate = [...currentBatch, repo];
    const encodedLength = encodeURIComponent(buildDraft(candidate)).length;
    if(currentBatch.length && (encodedLength > maxEncodedLength || candidate.length > maxItemsPerBatch)){
      batches.push(currentBatch);
      currentBatch = [repo];
    }else{
      currentBatch = candidate;
    }
  }
  if(currentBatch.length) batches.push(currentBatch);
  return batches.map((batch, index) => buildBatchPrompt(batch, title, index + 1, batches.length));
}

async function openExternalUrl(url){
  const target = String(url || "").trim();
  if(!target) return false;
  try{
    const {resp, data} = await requestJson(
      "/api/open-external",
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({url:target}),
      },
      "打开链接失败",
    );
    if(resp.ok && data.ok) return true;
  }catch(_err){}
  window.open(target, "_blank", "noopener");
  return true;
}

async function openAiPrompts(prompts){
  const queue = prompts.filter(Boolean);
  if(!queue.length) return false;
  if(aiTargets.has("copy")){
    await copyText(queue.join("\n\n-----\n\n"), "分析提示词已复制");
    return true;
  }
  const targets = [...aiTargets].filter(t => t !== "copy");
  if(!targets.length) return false;
  const aiNames = targets.map(t => AI_TARGET_LABELS[t] || t).join(" + ");
  await copyText(
    queue[queue.length - 1],
    queue.length === 1 ? `分析提示词已复制，正在打开 ${aiNames}` : `已准备 ${queue.length} 组提示词，正在批量打开 ${aiNames}`,
  );
  for(const target of targets){
    for(let index = 0; index < queue.length; index += 1){
      const {resp, data} = await requestJson(
        "/api/chatgpt/open",
        {
          method:"POST",
          headers:{"Content-Type":"application/json"},
          body:JSON.stringify({mode:target, prompt:queue[index]}),
        },
        `打开 ${AI_TARGET_LABELS[target] || target} 失败`,
      );
      if(!resp.ok || !data.ok){
        toast(data.error || `打开 ${AI_TARGET_LABELS[target] || target} 失败`);
        return false;
      }
      if(index < queue.length - 1 || targets.indexOf(target) < targets.length - 1) await sleep(300);
    }
  }
  toast(queue.length === 1 ? `已打开 ${aiNames}` : `已批量打开 ${queue.length} 组分析（${aiNames}）`);
  return true;
}

async function exportUserState(){
  try{
    const resp = await fetch("/api/export", {cache:"no-store"});
    if(!resp.ok) throw new Error("导出失败");
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `gitsonar-export-${new Date().toISOString().slice(0,10)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast("已导出数据");
  }catch(error){
    toast(error.message || "导出失败");
  }
}

function beginImportUserState(mode = "merge"){
  pendingImportMode = String(mode || "merge").trim() === "replace" ? "replace" : "merge";
  const input = document.getElementById("import-user-state-input");
  if(!input) return;
  input.value = "";
  input.click();
}

async function importUserStateFile(file){
  if(!file) return;
  let payload;
  try{
    payload = JSON.parse(await file.text());
  }catch(_err){
    toast("导入文件不是有效的 JSON");
    return;
  }
  try{
    const {resp, data} = await requestJson(
      "/api/import",
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({mode:pendingImportMode, data:payload}),
      },
      "导入失败",
    );
    if(!resp.ok || !data.ok){
      toast(data.error || "导入失败");
      return;
    }
    userState = data.user_state || userState;
    render();
    const before = data.before_counts || {};
    const after = data.after_counts || {};
    toast(`${pendingImportMode === "replace" ? "覆盖" : "合并"}导入完成：收藏 ${before.favorites || 0}→${after.favorites || 0}`);
  }catch(error){
    toast(error.message || "导入失败");
  }
}

function syncDiscoverDraftUI(){
  const queryNode = document.getElementById("discover-query");
  const languageNode = document.getElementById("discover-language");
  const limitNode = document.getElementById("discover-limit");
  const rankingProfileNode = document.getElementById("discover-ranking-profile");
  const autoExpandNode = document.getElementById("discover-auto-expand");
  const saveQueryNode = document.getElementById("discover-save-query");
  const runNode = document.getElementById("discover-run-btn");
  const cancelNode = document.getElementById("discover-cancel-btn");
  const clearNode = document.getElementById("discover-clear-btn");
  if(!queryNode) return;
  queryNode.value = discoverDraft.query || "";
  languageNode.value = discoverDraft.language || "";
  limitNode.value = discoverDraft.limit || 20;
  rankingProfileNode.value = normalizeDiscoveryRankingProfile(discoverDraft.rankingProfile);
  autoExpandNode.checked = !!discoverDraft.autoExpand;
  saveQueryNode.checked = !!discoverDraft.saveQuery;
  queryNode.disabled = discoveryBusy;
  languageNode.disabled = discoveryBusy;
  limitNode.disabled = discoveryBusy;
  rankingProfileNode.disabled = discoveryBusy;
  autoExpandNode.disabled = discoveryBusy;
  saveQueryNode.disabled = discoveryBusy;
  syncCustomSelect("discover-ranking-profile");
  if(clearNode) clearNode.disabled = discoveryBusy;
  if(cancelNode){
    cancelNode.hidden = !discoveryBusy;
    cancelNode.disabled = !discoveryBusy;
  }
  if(runNode){
    runNode.disabled = discoveryBusy || !String(discoverDraft.query || "").trim();
    runNode.textContent = discoveryBusy ? `${activeDiscoveryJob?.stage_label || "发现中"}...` : "开始发现";
  }
}

function renderSavedDiscoveryQueries(){
  const items = savedDiscoveryQueries();
  if(!items.length) return '<div class="discover-chip"><div class="discover-chip-note">还没有保存的搜索。</div></div>';
  const disabledAttr = discoveryBusy ? " disabled" : "";
  return items.map(item => `<div class="discover-chip">
    <div class="discover-chip-head">
      <div class="discover-chip-title">${h(item.query)}</div>
      ${item.language ? `<span class="badge source">${h(item.language)}</span>` : ""}
      <span class="badge">${h(discoveryRankingLabel(item.ranking_profile))}</span>
      ${item.auto_expand ? '<span class="badge gain">扩词</span>' : ""}
    </div>
    <div class="discover-chip-note">${h(item.last_run_at ? `上次运行 ${item.last_run_at}` : "尚未运行")}</div>
    <div class="discover-chip-actions">
      <button class="action-quiet" type="button" onclick='runSavedDiscovery(${JSON.stringify(item.id)})'${disabledAttr}>运行</button>
      <button class="action-quiet danger" type="button" onclick='deleteDiscoveryQuery(${JSON.stringify(item.id)})'${disabledAttr}>删除</button>
    </div>
  </div>`).join("");
}

function renderDiscoveryMeta(){
  const results = discoveryResults();
  const job = activeDiscoveryJob;
  const lastQuery = (job && job.query) || discoveryState.last_query || {};
  const rankingLabel = discoveryRankingLabel(lastQuery.ranking_profile || discoverDraft.rankingProfile);
  const tokenHint = settings.has_github_token ? "" : '<div class="reason-strip"><span class="reason-pill">未配置 GitHub Token，关键词发现结果可能更少且更容易触发限流。</span></div>';
  if(job){
    const warnings = Array.isArray(job.warnings) ? job.warnings : [];
    const generatedQueries = Array.isArray(job.generated_queries) ? job.generated_queries : [];
    const relatedTerms = Array.isArray(job.related_terms) ? job.related_terms : [];
    const elapsedSeconds = Number(job.elapsed_seconds || (discoveryStartedAt ? Math.max(1, Math.round((Date.now() - discoveryStartedAt) / 1000)) : 0));
    const etaInitialSeconds = Number(job.eta_initial_seconds || 0);
    const etaFullSeconds = Number(job.eta_full_seconds || 0);
    const etaRemainingSeconds = Number(job.eta_remaining_seconds || 0);
    const phaseCopy = discoveryBusy
      ? (results.length
        ? `已拿到 <strong>${results.length}</strong> 个首轮候选，完整扩词与重排预计还需 <strong>${etaRemainingSeconds || "?"}</strong> 秒。`
        : `首轮结果预计 <strong>${etaInitialSeconds || "?"}</strong> 秒内返回，完整结果预计 <strong>${etaFullSeconds || "?"}</strong> 秒左右。`)
      : "";
    const warningMarkup = warnings.length ? `<div class="reason-strip">${warnings.map(item => `<span class="reason-pill">${h(item)}</span>`).join("")}</div>` : "";
    return `<div class="discover-meta-card${discoveryBusy ? " loading" : ""}">
      <div class="discover-loading-row">
        ${discoveryBusy ? '<span class="discover-spinner" aria-hidden="true"></span>' : '<span class="reason-pill">任务结束</span>'}
        <div>
          <div class="discover-meta-title">${h(job.stage_label || "正在发现")}</div>
          <div><strong>${h(lastQuery.query || discoverDraft.query || "当前关键词")}</strong>${discoveryBusy ? ` 已运行约 <strong>${elapsedSeconds || 1}</strong> 秒。` : ""}${!discoveryBusy && job.message ? ` ${h(job.message)}` : ""}</div>
        </div>
      </div>
      <div class="discover-loading-copy">${phaseCopy || h(job.message || "当前会依次执行：首轮 GitHub Search、详情补全、扩词搜索、综合打分。")}</div>
      <div class="reason-strip">
        <span class="reason-pill">当前阶段：${h(job.stage_label || "-")}</span>
        <span class="reason-pill">排序模式：${h(rankingLabel)}</span>
        <span class="reason-pill">首轮预计：${etaInitialSeconds || "?"} 秒</span>
        <span class="reason-pill">完整预计：${etaFullSeconds || "?"} 秒</span>
        ${discoveryBusy ? `<span class="reason-pill">剩余约：${etaRemainingSeconds || "?"} 秒</span>` : ""}
      </div>
      ${relatedTerms.length ? `<div>相关词：${relatedTerms.map(term => `<span class="reason-pill">${h(term)}</span>`).join("")}</div>` : ""}
      ${generatedQueries.length ? `<div>实际查询：${generatedQueries.map(term => `<span class="reason-pill">${h(term)}</span>`).join("")}</div>` : ""}
      ${warningMarkup}
      ${tokenHint}
    </div>`;
  }
  if(!lastQuery.query && !results.length){
    return `<div class="discover-meta-card">输入关键词后，系统会自动扩展相关词并按综合分返回候选仓库。${tokenHint}</div>`;
  }
  const translated = discoveryState.last_translated_query || "";
  const relatedTerms = Array.isArray(discoveryState.last_related_terms) ? discoveryState.last_related_terms : [];
  const generatedQueries = Array.isArray(discoveryState.last_generated_queries) ? discoveryState.last_generated_queries : [];
  const warnings = Array.isArray(discoveryState.last_warnings) ? discoveryState.last_warnings : [];
  return `<div class="discover-meta-card">
    <div class="discover-meta-title">本次发现</div>
    <div>关键词：<strong>${h(lastQuery.query || "")}</strong>${translated ? ` · 英文扩展：<strong>${h(translated)}</strong>` : ""}</div>
    <div>结果数：<strong>${results.length}</strong>${discoveryState.last_run_at ? ` · 运行时间：<strong>${h(discoveryState.last_run_at)}</strong>` : ""}</div>
    <div>排序模式：<strong>${h(rankingLabel)}</strong></div>
    <div>${relatedTerms.length ? `相关词：${relatedTerms.map(term => `<span class="reason-pill">${h(term)}</span>`).join("")}` : "相关词：本次未生成扩展词"}</div>
    <div>${generatedQueries.length ? `实际查询：${generatedQueries.map(term => `<span class="reason-pill">${h(term)}</span>`).join("")}` : ""}</div>
    ${warnings.length ? `<div class="reason-strip">${warnings.map(item => `<span class="reason-pill">${h(item)}</span>`).join("")}</div>` : ""}
    ${tokenHint}
  </div>`;
}

function renderDiscoveryTop(){
  const top = discoveryResults().slice(0, 5);
  if(!top.length) return "";
  return `<div class="group-label">Top 5 推荐</div>
    <div class="discover-top-grid">
      ${top.map(repo => `<article class="discover-top-card">
        <div class="discover-top-rank">#${repo.rank || "-"}</div>
        <div class="discover-chip-title">${h(repo.full_name)}</div>
        <div class="discover-chip-note">综合 ${repo.composite_score || 0} · 相关 ${repo.relevance_score || 0} · 热度 ${repo.hot_score || 0}</div>
        <div class="reason-strip">${(repo.match_reasons || []).slice(0, 2).map(reason => `<span class="reason-pill">${h(reason)}</span>`).join("")}</div>
      </article>`).join("")}
    </div>`;
}

function syncDiscoveryPanel(){
  const savedNode = document.getElementById("discover-saved");
  const metaNode = document.getElementById("discover-meta");
  const topNode = document.getElementById("discover-top");
  if(!savedNode || !metaNode || !topNode) return;
  syncDiscoverDraftUI();
  savedNode.innerHTML = renderSavedDiscoveryQueries();
  metaNode.innerHTML = renderDiscoveryMeta();
  topNode.innerHTML = renderDiscoveryTop();
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
        "获取关键词发现进度失败",
      ));
    }catch(error){
      discoveryBusy = false;
      discoveryStartedAt = 0;
      activeDiscoveryJob = {
        id:jobId,
        status:"failed",
        stage:"failed",
        stage_label:"进度获取失败",
        message:error.message || "获取关键词发现进度失败",
        query:{...discoverDraft},
        warnings:[],
        preview_results:discoveryResults(),
      };
      render();
      toast(error.message || "获取关键词发现进度失败");
      return;
    }
    if(!resp.ok || !data.ok){
      discoveryBusy = false;
      discoveryStartedAt = 0;
      activeDiscoveryJob = {
        id:jobId,
        status:"failed",
        stage:"failed",
        stage_label:"进度获取失败",
        message:data.error || "获取关键词发现进度失败",
        query:{...discoverDraft},
        warnings:[],
        preview_results:discoveryResults(),
      };
      render();
      toast(data.error || "获取关键词发现进度失败");
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
      toast(`关键词发现已完成（约 ${job.elapsed_seconds || job.eta_full_seconds || "?"} 秒）`);
      return;
    }
    if(job.status === "failed"){
      discoveryBusy = false;
      discoveryStartedAt = 0;
      render();
      toast(job.error || job.message || "关键词发现失败");
      return;
    }
    if(job.status === "cancelled"){
      discoveryBusy = false;
      discoveryStartedAt = 0;
      render();
      toast(job.message || "已取消关键词发现");
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
      toast("关键词发现任务未返回有效 job");
      return;
    }
    applyActiveDiscoveryJob(job);
    render();
    toast(`${data.message || "关键词发现任务已开始"}，首轮约 ${job.eta_initial_seconds || "?"} 秒，完整约 ${job.eta_full_seconds || "?"} 秒`);
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
  await beginDiscoveryJob("/api/discover", payload, "关键词发现失败", "正在准备关键词发现任务");
}

async function runSavedDiscovery(queryId){
  await beginDiscoveryJob("/api/discovery/run-saved", {id:queryId}, "运行保存搜索失败", "正在重新运行已保存搜索");
}

async function cancelDiscovery(){
  const jobId = String(activeDiscoveryJob?.id || "").trim();
  if(!jobId){
    toast("当前没有可取消的关键词发现任务");
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
      "取消关键词发现失败",
    );
    if(!resp.ok || !data.ok){
      toast(data.error || "取消关键词发现失败");
      return;
    }
    if(data.job) applyActiveDiscoveryJob(data.job);
    render();
    toast(data.message || "已发送取消请求");
  }catch(error){
    toast(error.message || "取消关键词发现失败");
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
    const {resp, data} = await requestJson("/api/discovery/clear", {method:"POST"}, "清空发现结果失败");
    if(!resp.ok || !data.ok){
      toast(data.error || "清空发现结果失败");
      return;
    }
    discoveryState = data.discovery_state || {};
    activeDiscoveryJob = null;
    discoveryBusy = false;
    discoveryStartedAt = 0;
    render();
    toast(data.message || "已清空本次关键词发现结果");
  }catch(error){
    toast(error.message || "清空发现结果失败");
  }
}

function compareByKey(a, b, key){
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

function menuRoot(id){
  return document.querySelector(`[data-menu-id="${id}"]`);
}

function customSelectRoot(selectId){
  return document.querySelector(`[data-custom-select-for="${selectId}"]`);
}

function syncMenuTriggerState(root){
  if(!root) return;
  const expanded = root.classList.contains("open");
  root.querySelectorAll("[aria-haspopup]").forEach(node => {
    node.setAttribute("aria-expanded", expanded ? "true" : "false");
  });
}

function closeMenus(exceptId = ""){
  document.querySelectorAll("[data-menu-id].open").forEach(root => {
    if(root.dataset.menuId !== exceptId) root.classList.remove("open");
    syncMenuTriggerState(root);
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
  root.classList.toggle("open", willOpen);
  syncMenuTriggerState(root);
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
  if(select.disabled) root.classList.remove("open");

  panel.innerHTML = options.map(option => {
    const value = String(option.value ?? "");
    const label = String(option.textContent || "").trim() || value;
    const activeClass = value === currentValue ? " active" : "";
    const disabledAttr = option.disabled ? " disabled" : "";
    const selectedAttr = value === currentValue ? "true" : "false";
    return `<button class="menu-item${activeClass}" type="button" role="option" aria-selected="${selectedAttr}"${disabledAttr} onclick='setCustomSelectValue(${JSON.stringify(selectId)}, ${JSON.stringify(value)})'>${h(label)}</button>`;
  }).join("");

  syncMenuTriggerState(root);
}

function syncAllCustomSelects(){
  CUSTOM_SELECT_IDS.forEach(syncCustomSelect);
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
  let label;
  if(aiTargets.size === 1){
    const [only] = aiTargets;
    label = AI_TARGET_LABELS[only] || AI_TARGET_LABELS.web;
  } else if(aiTargets.size === 2){
    label = [...aiTargets].map(k => AI_TARGET_LABELS[k] || k).join(" + ");
  } else {
    label = `${aiTargets.size} 个 AI`;
  }
  document.getElementById("ai-target-label").textContent = label;
  document.querySelectorAll("[data-ai-target]").forEach(btn => {
    btn.classList.toggle("active", aiTargets.has(btn.dataset.aiTarget));
  });
}

function syncFilterPanel(){
  const filterPanel = document.getElementById("filter-panel");
  const filterToggle = document.getElementById("filter-toggle");
  const canUseFilters = panel !== UPDATE_PANEL_KEY && panel !== DISCOVER_PANEL_KEY;
  const isOpen = canUseFilters && filterPanelOpen;

  if(filterPanel){
    filterPanel.hidden = !canUseFilters;
    filterPanel.classList.toggle("is-open", isOpen);
  }
  if(filterToggle){
    filterToggle.hidden = !canUseFilters;
    filterToggle.disabled = !canUseFilters;
    filterToggle.classList.toggle("active", isOpen);
    filterToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
  }
}

function toggleFilterPanel(force){
  if(panel === UPDATE_PANEL_KEY || panel === DISCOVER_PANEL_KEY) return;
  filterPanelOpen = typeof force === "boolean" ? force : !filterPanelOpen;
  localStorage.setItem(FILTER_PANEL_STORAGE_KEY, filterPanelOpen ? "true" : "false");
  syncFilterPanel();
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
  stateFilterGroup.hidden = disableListControls;
  stateFilterGroup.classList.toggle("is-disabled", disableListControls);
  document.getElementById("sort-primary-group").classList.toggle("is-disabled", disableListControls);
  document.getElementById("clear-updates-menu-item").hidden = !isUpdatePanel || !(userState.favorite_updates || []).length;
  document.getElementById("discover-module").hidden = !isDiscoverPanel;
  syncFilterPanel();
  syncCustomSelect("language");
}

const emptyIcon = '<div style="display:flex; flex-direction:column; align-items:center; gap:24px; padding:64px 20px;"><div style="position:relative; width:80px; height:80px; border-radius:999px; background:radial-gradient(circle at center, rgba(233,201,143,0.08) 0%, transparent 70%); display:flex; align-items:center; justify-content:center;"><svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="rgba(233,201,143,0.24)" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M16 16s-1.5-2-4-2-4 2-4 2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line></svg></div></div>';

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
  return `<div class="desc-wrap"><div class="desc${muted ? " muted" : ""}">${safe}</div></div>`;
}

function refreshSelectionSummary(){
  const isUpdatePanel = panel === UPDATE_PANEL_KEY;
  const isDiscoverPanel = panel === DISCOVER_PANEL_KEY;
  const repos = visibleRepos();
  const updates = visibleUpdates();
  const selected = selectedCount();
  document.getElementById("visible-count").textContent = isUpdatePanel ? updates.length : repos.length;
  document.getElementById("visible-label").textContent = isUpdatePanel ? " 条更新" : (isDiscoverPanel ? " 个发现候选" : " 个仓库");
  document.getElementById("selected-count").textContent = selected;
  document.getElementById("batch-dock-count").textContent = selected;
  document.getElementById("compare-selected-btn").disabled = selectedRepos().length !== 2;
  document.getElementById("batch-dock").classList.toggle("show", selected > 0);
  document.body.classList.toggle("has-batch-dock", selected > 0);
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
  const data = isUpdatePanel ? visibleUpdates() : visibleRepos();
  const renderFn = isUpdatePanel ? renderUpdateCards : renderRepoCards;

  window.__lazyData = data;
  window.__lazyRenderFn = renderFn;
  window.__lazyIndex = 30;

  const container = document.getElementById("cards");
  container.innerHTML = renderFn(data.slice(0, window.__lazyIndex));
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
  document.getElementById("analyze-visible-btn").querySelector(".split-main-title").textContent = isDiscoverPanel ? "分析发现结果" : "分析当前列表";
  refreshSelectionSummary();
}

function setPanel(nextPanel){
  panel = normalizePanelKey(nextPanel || "daily");
  localStorage.setItem("gtr-tab", panel);
  closeMenus();
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
}

async function analyzeRepo(url){
  const repo = repoByUrl(url);
  if(!repo){
    toast("未找到仓库信息");
    return;
  }
  await openAiPrompts([buildRepoPrompt(repo)]);
}

async function analyzeVisible(){
  if(panel === UPDATE_PANEL_KEY){
    toast("收藏更新面板不支持整页分析");
    return;
  }
  const repos = visibleRepos().slice(0, 20);
  if(!repos.length){
    toast("当前列表没有可分析的仓库");
    return;
  }
  await openAiPrompts(splitRepoPrompts(repos, panel === DISCOVER_PANEL_KEY ? "当前关键词发现结果" : "当前 GitHub 趋势列表"));
}

async function analyzeSelected(){
  const repos = selectedRepos();
  if(!repos.length){
    toast("请先选中仓库");
    return;
  }
  await openAiPrompts(splitRepoPrompts(repos, "已选仓库"));
}

async function fetchRepoDetails(repo){
  const {resp, data} = await requestJson(`/api/repo-details?owner=${encodeURIComponent(repo.owner)}&name=${encodeURIComponent(repo.name)}`, {cache:"no-store"}, "仓库详情加载失败");
  if(!resp.ok || !data.ok) throw new Error(data.error || "详情获取失败");
  return data.details;
}

function buildComparePrompt(a, b, detailA, detailB){
  return `请用中文对比下面两个 GitHub 仓库，并输出：
1. 两个项目分别解决什么问题
2. 功能定位和差异化对比
3. 社区热度与活跃度对比
4. 各自更适合哪些用户和场景
5. 如果只能长期关注一个，更建议关注哪一个，为什么

项目 A
名称: ${a.full_name}
链接: ${a.url}
语言: ${a.language || "未知语言"}
Stars: ${detailA.stars || a.stars || 0}
Forks: ${detailA.forks || a.forks || 0}
最近推送: ${detailA.pushed_at || "未知"}
简介: ${detailA.description || detailA.description_raw || a.description || a.description_raw || "暂无描述"}
README 摘要: ${detailA.readme_summary || detailA.readme_summary_raw || "暂无"}

项目 B
名称: ${b.full_name}
链接: ${b.url}
语言: ${b.language || "未知语言"}
Stars: ${detailB.stars || b.stars || 0}
Forks: ${detailB.forks || b.forks || 0}
最近推送: ${detailB.pushed_at || "未知"}
简介: ${detailB.description || detailB.description_raw || b.description || b.description_raw || "暂无描述"}
README 摘要: ${detailB.readme_summary || detailB.readme_summary_raw || "暂无"}`;
}

function syncOverlayLock(){
  const hasVisibleOverlay = ["settings-modal", "detail-modal", "compare-modal"].some(id => document.getElementById(id)?.classList.contains("show"));
  document.body.classList.toggle("overlay-open", hasVisibleOverlay);
}

function setOverlayVisible(id, visible){
  const overlay = document.getElementById(id);
  if(!overlay) return;
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

const pendingStateRequests = new Set();

async function toggleState(key, url){
  const repo = repoByUrl(url);
  if(!repo) return;
  const requestKey = `${key}::${url}`;
  if(pendingStateRequests.has(requestKey)) return;
  pendingStateRequests.add(requestKey);
  const wasVisible = visibleLinkList().includes(url);
  const enabling = !((userState[key] || []).includes(url));
  try{
    const {resp, data} = await requestJson(
      "/api/state",
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({state:key, enabled:enabling, repo}),
      },
      "Update failed",
    );
    if(!resp.ok || !data.ok){
      toast(data.error || "Update failed");
      return;
    }
    userState = data.user_state;
    const isStillVisible = visibleLinkList().includes(url);
    renderTabs();
    if(wasVisible !== isStillVisible){
      cleanupSelected();
      refreshVisibleCards();
    }else{
      syncStateActionsForUrl(url);
    }
    refreshSelectionSummary();
    const githubStarSync = data.github_star_sync;
    if(key === "favorites" && githubStarSync?.message){
      toast(githubStarSync.message);
    }
  } finally {
    pendingStateRequests.delete(requestKey);
  }
}

async function batchSetState(stateKey){
  const repos = selectedRepos();
  if(!repos.length){
    toast("请先选中仓库再批量操作");
    return;
  }
  let lastState = null;
  for(const repo of repos){
    const {resp, data} = await requestJson(
      "/api/state",
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({state:stateKey, enabled:true, repo}),
      },
      "批量操作失败",
    );
    if(!resp.ok || !data.ok){
      toast(data.error || "批量操作失败");
      return;
    }
    if(data.user_state) lastState = data.user_state;
  }
  if(lastState) userState = lastState;
  const label = stateDefs().find(state => state.key === stateKey)?.label || stateKey;
  render();
  toast(`已将 ${repos.length} 个仓库加入“${label}”`);
}

async function syncGitHubStars(){
  toast("正在拉取 GitHub 星标，请稍候...");
  let resp, data;
  try{
    ({resp, data} = await requestJson("/api/sync-stars", {method:"POST"}, "同步失败，请检查网络和 Token 配置"));
  }catch(err){
    toast(err.message || "同步失败");
    return;
  }
  if(!resp.ok || !data.ok){
    toast(data.error || "同步失败");
    return;
  }
  if(data.user_state) userState = data.user_state;
  render();
  toast(data.message || "同步完成");
}

async function clearFavoriteUpdates(){
  if(!(userState.favorite_updates || []).length){
    toast("当前没有收藏更新记录");
    return;
  }
  if(!window.confirm("确认清空收藏更新记录吗？")) return;
  const {resp, data} = await requestJson("/api/favorite-updates/clear", {method:"POST"}, "清空收藏更新记录失败");
  if(!resp.ok || !data.ok){
    toast(data.error || "清空失败");
    return;
  }
  userState = data.user_state;
  render();
  toast(data.message || "已清空收藏更新记录");
}

async function refreshNow(){
  try{
    const {resp, data} = await requestJson("/api/refresh", {method:"POST"}, "刷新请求失败");
    if(!resp.ok || !data.ok){
      toast(data.error || "刷新失败");
      return;
    }
    currentNote = data.message || "已开始后台刷新。";
    render();
    poll();
  }catch(error){
    toast(error.message || "刷新失败");
  }
}

function poll(){
  clearInterval(window.__pollTimer);
  window.__pollTimer = setInterval(async() => {
    try{
      const {resp, data} = await requestJson(`/api/status?ts=${Date.now()}`, {cache:"no-store"}, "状态轮询失败");
      if(!resp.ok){
        currentNote = data.error || "状态获取失败";
        document.getElementById("note").textContent = currentNote;
        return;
      }
      currentNote = data.refreshing ? "后台刷新中..." : (data.error || "已显示最新数据");
      document.getElementById("note").textContent = currentNote;
      if(!data.refreshing){
        clearInterval(window.__pollTimer);
        location.reload();
      }
    }catch(error){
      currentNote = error.message || "状态轮询失败";
      document.getElementById("note").textContent = currentNote;
    }
  }, 1500);
}

async function hideToTray(){
  toast("当前版本已禁用系统托盘");
}

async function exitApp(){
  if(!window.confirm("确认直接退出 GitSonar 吗？")) return;
  try{
    const {resp, data} = await requestJson("/api/window/exit", {method:"POST"}, "退出程序失败");
    if(!resp.ok || !data.ok){
      toast(data.error || data.message || "退出程序失败");
      return;
    }
    toast(data.message || "正在退出程序");
    setTimeout(() => window.close(), 150);
  }catch(error){
    toast(error.message || "退出程序失败");
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
}

document.getElementById("cards").addEventListener("click", event => {
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

document.getElementById("discover-query").addEventListener("input", event => {
  discoverDraft.query = event.target.value;
  saveDiscoverDraft();
  syncDiscoverDraftUI();
});

document.getElementById("discover-language").addEventListener("input", event => {
  discoverDraft.language = event.target.value;
  saveDiscoverDraft();
});

document.getElementById("discover-limit").addEventListener("input", event => {
  const nextValue = Number(event.target.value || 20);
  discoverDraft.limit = Number.isFinite(nextValue) ? Math.max(5, Math.min(50, nextValue)) : 20;
  saveDiscoverDraft();
});

document.getElementById("discover-ranking-profile").addEventListener("change", event => {
  discoverDraft.rankingProfile = normalizeDiscoveryRankingProfile(event.target.value);
  saveDiscoverDraft();
});

document.getElementById("discover-auto-expand").addEventListener("change", event => {
  discoverDraft.autoExpand = !!event.target.checked;
  saveDiscoverDraft();
});

document.getElementById("discover-save-query").addEventListener("change", event => {
  discoverDraft.saveQuery = !!event.target.checked;
  saveDiscoverDraft();
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

document.addEventListener("click", event => {
  const externalTarget = event.target.closest("[data-external-url]");
  if(externalTarget){
    event.preventDefault();
    event.stopPropagation();
    openExternalUrl(externalTarget.getAttribute("data-external-url"));
    return;
  }
  if(!event.target.closest("[data-menu-id]")) closeMenus();
});

window.addEventListener("keydown", event => {
  if(event.key !== "Escape") return;
  closeMenus();
  closeSettings();
  closeDetail();
  closeCompare();
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
if(INITIAL.pending) poll();
"""
