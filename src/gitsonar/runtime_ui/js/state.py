#!/usr/bin/env python3
from __future__ import annotations

JS = r"""function current(key){
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

function rememberedDiscoveryQuery(){
  return discoveryState && typeof discoveryState.remembered_query === "object" ? discoveryState.remembered_query : {};
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
    source_key:"favorite_update",
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
      source_key:"local_state",
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
    if(String(repo?.source_key || "").trim() === "favorite_update") return "更新追踪项";
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
语言要求：直白、通俗，遇到复杂概念优先解释清楚，不要堆术语。

【仓库信息】
名称：${repo.full_name}
链接：${repo.url}
语言：${repo.language || "未知语言"}
总星标：${repo.stars || 0}
增长：${gainLabel(repo)}
来源：${repo.source_label || "未知来源"}
简介：${repo.description || repo.description_raw || "暂无描述"}

【输出结构】
1. 一句话大白话解释
2. 核心价值（2-3 条）
3. 坑和局限（不要客气）
4. 一个具体使用场景
5. 主流竞品对比
6. 决策建议（立刻试用 / 持续观察 / 特定场景再看）`;
}

function buildBatchPrompt(repos, title, batchIndex, batchCount){
  const groupNote = batchCount > 1 ? `\n（当前是第 ${batchIndex}/${batchCount} 组）` : "";
  return `你是一位资深架构师，正在帮团队快速筛选值得关注的开源项目。
请用中文对下方每个仓库分别输出简洁研判，语言直白、不堆术语。${groupNote}

分析范围：${title}

仓库列表：
${repos.map(repoLine).join("\n")}

【每个仓库输出以下 4 项，用仓库名作为小标题】
1. 一句话说清楚它是做什么的
2. 最大的实际价值或亮点（1-2 条，带场景）
3. 主要风险或局限
4. 决策建议：立刻试用 / 持续观察 / 暂时忽略（附一句理由）`;
}

function splitRepoPrompts(repos, title, maxEncodedLength = 2600, maxItemsPerBatch = 4){
  const normalized = repos.filter(Boolean);
  if(!normalized.length) return [];
  if(normalized.length === 1) return [buildRepoPrompt(normalized[0])];
  const batches = [];
  let currentBatch = [];
  const buildDraft = candidate => `你是一位资深架构师，正在帮团队快速筛选值得关注的开源项目。请用中文对下方每个仓库分别输出简洁研判。\n分析范围：${title}\n仓库列表：\n${candidate.map(repoLine).join("\n")}\n【每个仓库输出：1.一句话说明 2.亮点 3.风险 4.建议】`;
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
}"""
