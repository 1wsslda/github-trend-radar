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
}"""
