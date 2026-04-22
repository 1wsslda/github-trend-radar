#!/usr/bin/env python3
from __future__ import annotations

from ..prompt_profiles import LEARNING_PROMPT_SPEC_JSON

JS = r"""const LEARNING_PROMPT_SPEC = __LEARNING_PROMPT_SPEC__;

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

function rememberedDiscoveryQuery(){
  return discoveryState && typeof discoveryState.remembered_query === "object" ? discoveryState.remembered_query : {};
}

function savedDiscoveryViews(){
  return Array.isArray(discoveryState.saved_views) ? discoveryState.saved_views : [];
}

function repoAnnotationByUrl(url){
  return userState.repo_annotations?.[url] || {};
}

function repoTagsForUrl(url){
  return Array.isArray(repoAnnotationByUrl(url).tags) ? repoAnnotationByUrl(url).tags : [];
}

function repoNoteForUrl(url){
  return String(repoAnnotationByUrl(url).note || "").trim();
}

function aiInsightByUrl(url){
  return userState.ai_insights?.[url] || null;
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
    topics:[],
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
      topics:[],
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

function joinPromptSections(sections){
  return sections.filter(section => String(section || "").trim()).join("\n\n");
}

function repoLine(repo){
  return `- ${repo.full_name} | ${repo.language || "未知语言"} | Stars ${repo.stars || 0} | ${repo.url}\n  简介: ${repo.description || repo.description_raw || "暂无描述"}`;
}

function collectionRepoLine(repo, index){
  const tags = repoTagsForUrl(repo.url);
  const note = repoNoteForUrl(repo.url);
  return `${index + 1}. ${repo.full_name} | ${repo.language || "未知语言"} | Stars ${repo.stars || 0} | ${repo.url}\n   增长: ${gainLabel(repo)}\n   来源: ${repo.source_label || "未知来源"}\n   简介: ${repo.description || repo.description_raw || "暂无描述"}${tags.length ? `\n   标签: ${tags.join(" / ")}` : ""}${note ? `\n   笔记: ${note}` : ""}`;
}

function learningPromptSection(name){
  return LEARNING_PROMPT_SPEC && typeof LEARNING_PROMPT_SPEC[name] === "object" ? LEARNING_PROMPT_SPEC[name] : {};
}

function promptSectionText(section, key){
  return String(learningPromptSection(section)?.[key] || "").trim();
}

function learnerGoalBlock(){
  return `【我的目标】
- 我现在是在学习较新的技术。
- 我想吸收优秀 GitHub 项目的设计、实现和产品思路。
- 我的最终目标不是复述仓库，而是做出属于自己的版本。`;
}

function learningLanguageRules(extraLines = []){
  const lines = [
    "- 必须用中文回答。",
    "- 遇到术语时，先解释它是什么意思，再继续分析。",
    "- 重点讲清楚：它解决什么问题、为什么这样设计、我能借鉴什么。",
    "- 如果某部分没有核验，直接标注“当前未核验”或“当前信息不足”。",
    "- 不要写成高管汇报、商业计划、采购建议或宣传文案。",
    "- 需要时可以用简单类比帮助理解，但不要喧宾夺主。",
  ];
  if(Array.isArray(extraLines) && extraLines.length){
    lines.push(...extraLines.filter(Boolean));
  }
  return `【表达要求】\n${lines.join("\n")}`;
}

function repoFactsBlock(repo){
  const tags = repoTagsForUrl(repo.url);
  const note = repoNoteForUrl(repo.url);
  return `【仓库信息】
名称：${repo.full_name}
链接：${repo.url}
语言：${repo.language || "未知语言"}
总星标：${repo.stars || 0}
增长：${gainLabel(repo)}
来源：${repo.source_label || "未知来源"}
简介：${repo.description || repo.description_raw || "暂无描述"}${tags.length ? `\n标签：${tags.join(" / ")}` : ""}${note ? `\n笔记：${note}` : ""}`;
}

function compareRepoFactsBlock(title, repo, detail){
  return `【${title}】
名称：${repo.full_name}
链接：${repo.url}
语言：${repo.language || "未知语言"}
总星标：${detail.stars || repo.stars || 0}
Forks：${detail.forks || repo.forks || 0}
最近推送：${detail.pushed_at || "未知"}
来源：${repo.source_label || "未知来源"}
简介：${detail.description || detail.description_raw || repo.description || repo.description_raw || "暂无描述"}
README 摘要：${detail.readme_summary || detail.readme_summary_raw || "暂无"}`;
}

function collectionHardRules(){
  return `【硬性要求】
1. 必须覆盖列表中的全部仓库，不得省略，不得合并跳过。
2. 输出顺序必须与输入列表保持一致。
3. 每个仓库都要单独给出判断，最后再给出整体学习路线建议。
4. 如果信息不足，必须明确写“当前未核验”或“当前信息不足”。
5. 不要按商业价值排序，而要按“值不值得学、值不值得借鉴、适不适合现在动手”来判断。`;
}

function compareHardRules(){
  return `【硬性要求】
1. 不要只比较谁更强，要比较各自更值得借鉴什么、哪里不该直接照搬。
2. 如果某个结论缺少仓库证据，必须明确写“当前未核验”或“当前信息不足”。
3. 最后必须落到动作建议：我应该先重点学哪个，先做哪个部分。`;
}

function buildRepoPrompt(repo){
  const repoInfo = repoFactsBlock(repo);
  return joinPromptSections([
    promptSectionText("repo", "role"),
    promptSectionText("repo", "intro"),
    promptSectionText("repo", "research_rules"),
    learningLanguageRules(),
    promptSectionText("repo", "rules"),
    promptSectionText("repo", "output"),
    promptSectionText("repo", "length"),
    repoInfo,
    learnerGoalBlock(),
  ]);
}

function buildCollectionPromptText(normalized, title, groupNote = ""){
  return joinPromptSections([
    `${promptSectionText("collection", "role")}${groupNote}`,
    promptSectionText("collection", "intro"),
    promptSectionText("collection", "research_rules"),
    learningLanguageRules([
      "- 批量分析时不要平均用力，重点挑出最值得深读和最该暂缓的项目。",
    ]),
    collectionHardRules(),
    promptSectionText("collection", "focus"),
    `分析范围：${title}
仓库数量：${normalized.length}`,
    `仓库列表：
${normalized.map(collectionRepoLine).join("\n")}`,
    `【输出结构】
${promptSectionText("collection", "structure")}`,
    promptSectionText("collection", "length"),
    learnerGoalBlock(),
  ]);
}

function buildBatchPrompt(repos, title, batchIndex, batchCount){
  const normalized = repos.filter(Boolean);
  if(!normalized.length) return "";
  const groupNote = batchCount > 1 ? `\n（当前是第 ${batchIndex}/${batchCount} 组）` : "";
  return buildCollectionPromptText(normalized, title, groupNote);
}

function buildCollectionPrompt(repos, title){
  const normalized = repos.filter(Boolean);
  if(!normalized.length) return "";
  return buildCollectionPromptText(normalized, title, "");
}

function compareLanguageRules(){
  return learningLanguageRules([
    "- 对比时不要只列功能点，要落到设计取舍、实现思路和可借鉴价值。",
  ]);
}

function compareResearchRules(){
  return promptSectionText("compare", "research_rules");
}

function compareProfileFocus(){
  return promptSectionText("compare", "focus");
}

function compareProfileStructure(){
  return promptSectionText("compare", "structure");
}

function compareLengthGuidance(){
  return promptSectionText("compare", "length");
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
}

function buildRepoMarkdownSummary(repo, detail = null){
  const target = detail && typeof detail === "object" ? detail : {};
  const tags = repoTagsForUrl(repo.url);
  const note = repoNoteForUrl(repo.url);
  const topics = Array.isArray(target.topics) ? target.topics.filter(Boolean) : (Array.isArray(repo.topics) ? repo.topics.filter(Boolean) : []);
  const lines = [
    `# ${repo.full_name}`,
    "",
    `- 链接：${repo.url}`,
    `- 语言：${repo.language || target.language || "未知"}`,
    `- 星标：${target.stars || repo.stars || 0}`,
    `- Forks：${target.forks || repo.forks || 0}`,
    `- 来源：${repo.source_label || "GitHub"}`,
    `- 最近推送：${target.pushed_at || repo.pushed_at || "未知"}`,
  ];
  if(target.latest_release_tag) lines.push(`- 最新版本：${target.latest_release_tag}`);
  if(tags.length) lines.push(`- 标签：${tags.join(" / ")}`);
  lines.push("");
  lines.push("## 简介");
  lines.push("");
  lines.push(target.description || target.description_raw || repo.description || repo.description_raw || "暂无简介");
  if(topics.length){
    lines.push("");
    lines.push("## Topics");
    lines.push("");
    lines.push(topics.map(topic => `- ${topic}`).join("\n"));
  }
  if(target.readme_summary || target.readme_summary_raw){
    lines.push("");
    lines.push("## README 摘要");
    lines.push("");
    lines.push(target.readme_summary || target.readme_summary_raw);
  }
  if(note){
    lines.push("");
    lines.push("## 我的笔记");
    lines.push("");
    lines.push(note);
  }
  return lines.join("\n");
}"""

JS = JS.replace("__LEARNING_PROMPT_SPEC__", LEARNING_PROMPT_SPEC_JSON)
