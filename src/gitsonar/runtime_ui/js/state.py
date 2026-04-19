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

function collectionRepoLine(repo, index){
  return `${index + 1}. ${repo.full_name} | ${repo.language || "\u672a\u77e5\u8bed\u8a00"} | Stars ${repo.stars || 0} | ${repo.url}\n   \u589e\u957f: ${gainLabel(repo)}\n   \u6765\u6e90: ${repo.source_label || "\u672a\u77e5\u6765\u6e90"}\n   \u7b80\u4ecb: ${repo.description || repo.description_raw || "\u6682\u65e0\u63cf\u8ff0"}`;
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
}

function buildCollectionPrompt(repos, title){
  const normalized = repos.filter(Boolean);
  if(!normalized.length) return "";
  return `\u4f60\u662f\u4e00\u4f4d\u8d44\u6df1\u67b6\u6784\u5e08\uff0c\u6b63\u5728\u5e2e\u56e2\u961f\u5feb\u901f\u7b5b\u9009\u503c\u5f97\u5173\u6ce8\u7684 GitHub \u5f00\u6e90\u9879\u76ee\u3002
\u8bf7\u7528\u4e2d\u6587\u4e25\u683c\u6309\u7ed9\u5b9a\u987a\u5e8f\uff0c\u9010\u4e2a\u5206\u6790\u4e0b\u9762\u7684\u4ed3\u5e93\uff0c\u8bed\u8a00\u76f4\u767d\uff0c\u4e0d\u5806\u672f\u8bed\u3002

\u3010\u786c\u6027\u8981\u6c42\u3011
1. \u5fc5\u987b\u8986\u76d6\u5217\u8868\u4e2d\u7684\u5168\u90e8\u4ed3\u5e93\uff0c\u4e0d\u5f97\u7701\u7565\uff0c\u4e0d\u5f97\u5408\u5e76\u8df3\u8fc7\u3002
2. \u8f93\u51fa\u987a\u5e8f\u5fc5\u987b\u4e0e\u8f93\u5165\u5217\u8868\u4fdd\u6301\u4e00\u81f4\u3002
3. \u6bcf\u4e2a\u4ed3\u5e93\u90fd\u8981\u5355\u72ec\u7ed9\u51fa\u7ed3\u8bba\uff0c\u6700\u540e\u518d\u7ed9\u51fa\u4e00\u6bb5\u6574\u4f53\u5efa\u8bae\u3002

\u5206\u6790\u8303\u56f4: ${title}
\u4ed3\u5e93\u6570\u91cf: ${normalized.length}

\u4ed3\u5e93\u5217\u8868:
${normalized.map(collectionRepoLine).join("\n")}

\u3010\u8f93\u51fa\u7ed3\u6784\u3011
1. \u6309\u8f93\u5165\u987a\u5e8f\uff0c\u4e3a\u6bcf\u4e2a\u4ed3\u5e93\u5206\u522b\u8f93\u51fa:
   - \u4e00\u53e5\u8bdd\u8bf4\u6e05\u695a\u5b83\u662f\u505a\u4ec0\u4e48\u7684
   - \u6700\u5927\u7684\u5b9e\u9645\u4ef7\u503c\u6216\u4eae\u70b9\uff081-2 \u6761\uff0c\u5e26\u573a\u666f\uff09
   - \u4e3b\u8981\u98ce\u9669\uff0c\u5c40\u9650\u6216\u91c7\u7528\u95e8\u69db
   - \u51b3\u7b56\u5efa\u8bae\uff1a\u7acb\u5373\u8bd5\u7528 / \u6301\u7eed\u89c2\u5bdf / \u6682\u65f6\u5ffd\u7565\uff0c\u5e76\u9644\u4e00\u53e5\u7406\u7531
2. \u6700\u540e\u8865\u4e00\u6bb5\u300a\u603b\u89c8\u5efa\u8bae\u300b\uff0c\u8bf4\u660e\u8fd9\u6279\u4ed3\u5e93\u91cc\u6700\u503c\u5f97\u4f18\u5148\u770b\u7684\u5bf9\u8c61\uff0c\u9002\u5408\u8c01\uff0c\u4ee5\u53ca\u4e0d\u8be5\u76f2\u76ee\u6295\u5165\u7684\u70b9\u3002`;
}

function canTransportAsSinglePrompt(prompt){
  prompt = String(prompt || "");
  return encodeURIComponent(prompt).length <= 2600;
}

function buildAnalysisMarkdown(title, prompt, repos){
  const normalized = repos.filter(Boolean);
  const lines = [
    `# GitSonar \u5206\u6790\u5bfc\u51fa\uff1a${title}`,
    "",
    `\u751f\u6210\u65f6\u95f4\uff1a${new Date().toISOString()}`,
    `\u4ed3\u5e93\u6570\u91cf\uff1a${normalized.length}`,
    "",
    "## \u4ed3\u5e93\u6e05\u5355",
    ...normalized.flatMap((repo, index) => [collectionRepoLine(repo, index), ""]),
    "## \u5b8c\u6574\u539f\u59cb prompt",
    "~~~~text",
    String(prompt || "").replace(/\r\n?/g, "\n"),
    "~~~~",
    "",
  ];
  return lines.join("\n");
}"""
