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

function promptSharedRules(){
  return `【通用要求】
- 只用中文。
- 按“15 岁学生也能看懂”的标准写。
- 遇到术语时，先用一句大白话解释，再继续。
- 不允许只说“值得关注”这类空话，必须说明“为什么”。
- 如果信息不够，必须明确写出“信息不够，下面是基于现有信息的判断”。
- 不要假装看过代码或文档里没有给出的信息。
- 结尾必须单独输出两个小节：一句话结论、下一步怎么做。`;
}

function promptProfileSingleFocus(profile){
  const activeProfile = normalizePromptProfile(profile);
  if(activeProfile === "understand"){
    return "先把项目讲明白，再判断它值不值得继续看。";
  }
  if(activeProfile === "adopt"){
    return "先判断能不能落地，再给出试用、PoC 和正式使用前的动作。";
  }
  return "先判断“我现在能不能用、适不适合我、怎么快速开始试”。";
}

function promptProfileBatchFocus(profile){
  const activeProfile = normalizePromptProfile(profile);
  if(activeProfile === "understand"){
    return "优先把每个项目讲明白，再判断要不要继续投入时间。";
  }
  if(activeProfile === "adopt"){
    return "优先找出更容易试用、做 PoC、再进入正式落地的项目。";
  }
  return "优先找出现在就值得试、并且最容易快速上手的项目。";
}

function promptProfileBatchLimit(profile){
  const activeProfile = normalizePromptProfile(profile);
  if(activeProfile === "adopt") return 2;
  if(activeProfile === "understand") return 4;
  return 3;
}

function repoFactsBlock(repo){
  return `名称：${repo.full_name}
链接：${repo.url}
语言：${repo.language || "未知语言"}
总星标：${repo.stars || 0}
增长：${gainLabel(repo)}
来源：${repo.source_label || "未知来源"}
简介：${repo.description || repo.description_raw || "暂无描述"}`;
}

function repoLine(repo){
  return `- ${repo.full_name} | ${repo.language || "未知语言"} | 星标 ${repo.stars || 0} | 增长 ${gainLabel(repo)} | 来源 ${repo.source_label || "未知来源"} | ${repo.url}\n  简介: ${repo.description || repo.description_raw || "暂无描述"}`;
}

function buildRepoPrompt(repo, profile){
  const activeProfile = normalizePromptProfile(profile);
  const header = `你是一位会给初学者讲清楚开源项目的技术顾问。请基于下面仓库信息，用中文给出详细、直白、可执行的分析。

【当前分析方式】
${promptProfileLabel(activeProfile)}：${promptProfileDescription(activeProfile)}

${promptSharedRules()}

【仓库信息】
${repoFactsBlock(repo)}

【这次分析的重点】
${promptProfileSingleFocus(activeProfile)}
`;

  if(activeProfile === "understand"){
    return `${header}
【输出结构】
1. 一句话大白话解释
2. 核心概念拆开讲清楚
3. 大家为什么会用它
4. 它和常见替代方案差在哪
5. 什么情况下根本不需要它
6. 如果你是新手，值不值得花时间看
7. 最后给结论和下一步

【最后必须追加两个小节】
- 一句话结论
- 下一步怎么做`;
  }

  if(activeProfile === "adopt"){
    return `${header}
【输出结构】
1. 适不适合放进真实项目
2. 需要满足哪些前提
3. 10 分钟 Demo 路线
4. 1 天 PoC 路线
5. 正式落地前检查清单
6. 失败时怎么退出或换方案
7. 最终结论和建议动作

【最后必须追加两个小节】
- 一句话结论
- 下一步怎么做`;
  }

  return `${header}
【输出结构】
1. 这个项目到底是干什么的
2. 它主要帮人解决什么问题
3. 最适合哪些人/团队
4. 明确不适合哪些人/场景
5. 你现在能不能上手用
6. 如果要试，最值得试的 3 个用法
7. 10 分钟快速试用方案
8. 1 天内验证值不值得继续的方案
9. 风险、坑、隐性成本
10. 最终判断
   - 只能从“现在就试 / 先收藏观察 / 暂时别用”里选一个，并说明原因

【最后必须追加两个小节】
- 一句话结论
- 下一步怎么做`;
}

function buildBatchPrompt(repos, title, batchIndex, batchCount, profile){
  const activeProfile = normalizePromptProfile(profile);
  const groupNote = batchCount > 1 ? `\n（当前是第 ${batchIndex}/${batchCount} 组）` : "";
  return `你是一位会给初学者讲清楚开源项目的技术顾问，正在帮用户从一组 GitHub 仓库里判断“先看谁、先试谁”。请用中文输出详细、直白、可执行的分析。${groupNote}

【当前分析方式】
${promptProfileLabel(activeProfile)}：${promptProfileDescription(activeProfile)}

${promptSharedRules()}

【这次分析的偏重点】
${promptProfileBatchFocus(activeProfile)}

【分析范围】
${title}

【仓库列表】
${repos.map(repoLine).join("\n")}

【对每个仓库都必须输出下面 6 项，并用仓库名作为小标题】
1. 它是什么
2. 适合谁
3. 不适合谁
4. 值不值得马上试，为什么
5. 如果值得试，第一步怎么试；如果不值得，为什么先跳过
6. 结论标签：只能从“优先试 / 先观察 / 先跳过”里选一个

【整组最后必须追加总评】
1. 最值得先看/先试的项目
2. 为什么是这几个
3. 如果我时间只有 1 小时，先看哪一个

【最后必须追加两个小节】
- 一句话结论
- 下一步怎么做`;
}

function splitRepoPrompts(repos, title, maxEncodedLength = 2600, maxItemsPerBatch = null, profile = promptProfile){
  const activeProfile = normalizePromptProfile(profile);
  const normalized = repos.filter(Boolean);
  if(!normalized.length) return [];
  if(normalized.length === 1) return [buildRepoPrompt(normalized[0], activeProfile)];
  const lengthLimit = Number.isFinite(Number(maxEncodedLength)) && Number(maxEncodedLength) > 0 ? Number(maxEncodedLength) : 2600;
  const batchLimit = Number.isFinite(Number(maxItemsPerBatch)) && Number(maxItemsPerBatch) > 0
    ? Number(maxItemsPerBatch)
    : promptProfileBatchLimit(activeProfile);
  const batches = [];
  let currentBatch = [];
  const buildDraft = candidate => buildBatchPrompt(candidate, title, 1, 2, activeProfile);
  for(const repo of normalized){
    const candidate = [...currentBatch, repo];
    const encodedLength = encodeURIComponent(buildDraft(candidate)).length;
    if(currentBatch.length && (encodedLength > lengthLimit || candidate.length > batchLimit)){
      batches.push(currentBatch);
      currentBatch = [repo];
    }else{
      currentBatch = candidate;
    }
  }
  if(currentBatch.length) batches.push(currentBatch);
  return batches.map((batch, index) => buildBatchPrompt(batch, title, index + 1, batches.length, activeProfile));
}"""
