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

function joinPromptSections(sections){
  return sections.filter(section => String(section || "").trim()).join("\n\n");
}

function repoLine(repo){
  return `- ${repo.full_name} | ${repo.language || "未知语言"} | Stars ${repo.stars || 0} | ${repo.url}\n  简介: ${repo.description || repo.description_raw || "暂无描述"}`;
}

function collectionRepoLine(repo, index){
  return `${index + 1}. ${repo.full_name} | ${repo.language || "未知语言"} | Stars ${repo.stars || 0} | ${repo.url}\n   增长: ${gainLabel(repo)}\n   来源: ${repo.source_label || "未知来源"}\n   简介: ${repo.description || repo.description_raw || "暂无描述"}`;
}

function audienceBlock(text = "非技术背景的业务高管"){
  return `【汇报对象】\n${text}`;
}

function companyBackgroundBlock(){
  return `【公司背景】\n如无特别说明，请默认按一家中大型企业评估，关注业务价值、落地成本、安全风险、团队投入和是否值得试点。`;
}

function bannedWordsLines(){
  return [
    "- 不要使用这些词：",
    "  解耦、赋能、底层逻辑、抓手、闭环、范式、壁垒、飞轮、生态位、全链路",
  ];
}

function commonLanguageRules(extraLines = [], includeWorkflowLine = true){
  const lines = [
    "- 必须极度通俗。",
    "- 不讲技术黑话。",
    "- 技术概念必须用生活化类比解释。",
    "- AI 代理 = 像一个会按目标办事的助理。",
    "- 大模型 = 像一个知识很广、但需要人检查的实习顾问。",
  ];
  if(includeWorkflowLine){
    lines.push("- 多个工具或流程配合 = 像把员工、表格、系统和审批步骤串成一条办事线。");
  }
  if(Array.isArray(extraLines) && extraLines.length){
    lines.push(...extraLines.filter(Boolean));
  }
  lines.push(...bannedWordsLines());
  return `【语言要求】\n${lines.join("\n")}`;
}

function officeLanguageRules(){
  return commonLanguageRules([
    "- 遇到 AI 代理、大模型、自动化流程等概念时，也可以类比成办公室助理、外包团队、工厂流水线或表格审批。",
  ]);
}

function truthRules(){
  return `【真实性要求】
- 只能基于给定信息做判断。
- 如果信息不足，必须明确写“当前信息不足以确认”。
- 不得脑补仓库没有体现的功能。
- 不得把教程说成产品。
- 不得把演示样例说成可直接上线系统。`;
}

function webResearchRules(){
  return `【必须先核验的信息】
1. README：确认项目到底是教程、样例、框架、工具还是产品。
2. 目录结构：判断它偏教学内容、代码模板，还是可运行系统。
3. 最近更新时间：判断项目是否活跃。
4. Issue 和 Pull Request：判断社区问题、维护状态和风险。
5. License：判断企业使用是否有潜在限制。
6. 依赖和运行方式：判断落地门槛。
7. 官方说明：确认项目作者对项目定位的描述。
8. 如有必要，查找同类方案或替代品进行对比。

【重要规则】
- 所有关键判断必须来自你查到的信息。
- 如果无法确认，必须写“无法从公开信息确认”。
- 不得把教程项目说成企业级产品。
- 不得因为星标高就判断它成熟。
- 星标只能代表关注度，不能代表可商用程度。

【引用要求】
- 报告中涉及项目事实、活跃度、License、维护状态、替代品时，需要给出来源。
- 如果当前环境不能联网，也必须明确写“无法从公开信息确认”。`;
}

function repoFactsBlock(repo){
  return `【仓库信息】
名称：${repo.full_name}
链接：${repo.url}
语言：${repo.language || "未知语言"}
总星标：${repo.stars || 0}
增长：${gainLabel(repo)}
来源：${repo.source_label || "未知来源"}
简介：${repo.description || repo.description_raw || "暂无描述"}`;
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

const DEFAULT_COLLECTION_PROMPT_CONFIG = {
  role:"你是一位懂商业、懂技术、也懂企业落地的技术总监兼产品战略负责人。",
  language_rules:{kind:"common", include_workflow_line:false, extra_lines:[]},
  focus:`【当前分析重点】
- 你的任务不是逐个做技术介绍，而是做项目筛选。
- 重点判断它到底是什么、能解决什么业务问题、更像学习资料/演示样例/开发工具/成熟产品、是否值得企业投入人力试用，以及最大风险是什么。`,
  structure:`第一部分：总览表
请输出表格，字段包括：
- 项目名称
- 一句话说明
- 项目类型
- 业务价值评分
- 落地难度评分
- 成熟度评分
- 最大风险
- 建议动作

建议动作只能从以下选项中选择：
- 立即试用
- 内部学习
- 持续观察
- 暂不投入
- 特定场景再看

第二部分：重点项目点评
只挑出最值得关注的前 3 个项目，每个项目用 4 段说明：
1. 为什么值得看
2. 能用在哪个业务场景
3. 最大坑在哪里
4. 下一步怎么试

第三部分：不建议投入项目
列出不建议投入的项目，并说明一句话原因。

第四部分：最终建议
用高管能理解的话总结：
- 哪个项目最值得近期安排人看
- 哪个项目适合内部培训
- 哪个项目只是热闹，不值得现在投人`,
};

const DEFAULT_COMPARE_PROMPT_CONFIG = {
  language_rules:{kind:"common", include_workflow_line:false, extra_lines:[]},
  focus:`【比较重点】
请比较：
1. 哪个更成熟？
2. 哪个更省事？
3. 哪个更适合企业正式使用？
4. 哪个更适合学习和试点？
5. 哪个风险最大？
6. 哪个近期最值得投入？`,
  structure:`1. 一句话结论
直接说最推荐哪个方向，以及为什么。

2. 对比表
字段包括：
- 方案名称
- 更像什么
- 适合用途
- 成熟度
- 使用成本
- 最大风险
- 适合谁

3. 逐项点评
每个方案用 3–5 句话说明：
- 优点
- 缺点
- 适合场景
- 不适合场景

4. 企业选择建议
分情况建议：
- 只是学习：选什么
- 做内部试点：选什么
- 上生产：选什么
- 没有技术团队：选什么

5. 最终建议
只能选一个：
- 优先用项目 A
- 优先用项目 B
- 优先买成熟产品
- 先学习再试点
- 暂不投入`,
};

function mergeProfileLanguageRules(baseConfig, overrideConfig){
  const base = baseConfig && typeof baseConfig === "object" ? baseConfig : {};
  const override = overrideConfig && typeof overrideConfig === "object" ? overrideConfig : {};
  return {
    kind:String(override.kind || base.kind || "common").trim() || "common",
    extra_lines:Array.isArray(override.extra_lines) ? override.extra_lines : (Array.isArray(base.extra_lines) ? base.extra_lines : []),
    include_workflow_line:
      override.include_workflow_line !== undefined
        ? !!override.include_workflow_line
        : (base.include_workflow_line !== undefined ? !!base.include_workflow_line : true),
  };
}

function promptProfileSectionConfig(profile, section, fallbackConfig = {}){
  const activeDefinition = promptProfileDefinition(profile);
  const activeConfig = activeDefinition?.[section] && typeof activeDefinition[section] === "object" ? activeDefinition[section] : {};
  const fallback = fallbackConfig && typeof fallbackConfig === "object" ? fallbackConfig : {};
  return {
    ...fallback,
    ...activeConfig,
    language_rules: mergeProfileLanguageRules(fallback.language_rules, activeConfig.language_rules),
  };
}

function resolvePromptProfileText(value){
  const text = String(value || "").trim();
  if(!text) return "";
  if(text === "__WEB_RESEARCH_RULES__") return webResearchRules();
  if(text === "__TRUTH_RULES__") return truthRules();
  return text;
}

function buildPromptLanguageRules(config, fallbackKind = "common", fallbackIncludeWorkflowLine = true){
  const merged = mergeProfileLanguageRules(
    {kind:fallbackKind, include_workflow_line:fallbackIncludeWorkflowLine, extra_lines:[]},
    config,
  );
  if(merged.kind === "office") return officeLanguageRules();
  return commonLanguageRules(merged.extra_lines, merged.include_workflow_line);
}

function buildRepoPrompt(repo, profile){
  const activeProfile = normalizePromptProfile(profile);
  const repoSpec = promptProfileDefinition(activeProfile).repo || {};
  const repoInfo = repoFactsBlock(repo);
  return joinPromptSections([
    resolvePromptProfileText(repoSpec.role),
    resolvePromptProfileText(repoSpec.intro),
    resolvePromptProfileText(repoSpec.focus),
    buildPromptLanguageRules(repoSpec.language_rules, "common", true),
    resolvePromptProfileText(repoSpec.rules),
    resolvePromptProfileText(repoSpec.output),
    resolvePromptProfileText(repoSpec.length),
    repoInfo,
    audienceBlock(resolvePromptProfileText(repoSpec.audience) || undefined),
    companyBackgroundBlock(),
  ]);
}

function batchProfileRole(profile){
  const collectionSpec = promptProfileSectionConfig(profile, "collection", DEFAULT_COLLECTION_PROMPT_CONFIG);
  return resolvePromptProfileText(collectionSpec.role || DEFAULT_COLLECTION_PROMPT_CONFIG.role);
}

function batchLanguageRules(profile){
  const collectionSpec = promptProfileSectionConfig(profile, "collection", DEFAULT_COLLECTION_PROMPT_CONFIG);
  return buildPromptLanguageRules(collectionSpec.language_rules, "common", false);
}

function batchProfileFocus(profile){
  const collectionSpec = promptProfileSectionConfig(profile, "collection", DEFAULT_COLLECTION_PROMPT_CONFIG);
  return resolvePromptProfileText(collectionSpec.focus || DEFAULT_COLLECTION_PROMPT_CONFIG.focus);
}

function batchProfileStructure(profile){
  const collectionSpec = promptProfileSectionConfig(profile, "collection", DEFAULT_COLLECTION_PROMPT_CONFIG);
  return resolvePromptProfileText(collectionSpec.structure || DEFAULT_COLLECTION_PROMPT_CONFIG.structure);
}

function buildCollectionPromptText(normalized, title, profile, groupNote = ""){
  const activeProfile = normalizePromptProfile(profile);
  return joinPromptSections([
    `${batchProfileRole(activeProfile)}${groupNote}`,
    "我会给你多个 GitHub 开源项目。请你站在企业业务高管视角，帮我快速筛选哪些值得关注、哪些只是看起来热闹。",
    `【当前分析方式】
${promptProfileLabel(activeProfile)}：${promptProfileDescription(activeProfile)}`,
    `【硬性要求】
1. 必须覆盖列表中的全部仓库，不得省略，不得合并跳过。
2. 输出顺序必须与输入列表保持一致。
3. 每个仓库都要单独给出结论，最后再给出一段整体建议。
4. 星标高只代表关注度，不代表成熟度。
5. 如果信息不足，必须明确写“当前信息不足以确认”。`,
    batchLanguageRules(activeProfile),
    batchProfileFocus(activeProfile),
    `分析范围：${title}
仓库数量：${normalized.length}`,
    `仓库列表：
${normalized.map(collectionRepoLine).join("\n")}`,
    `【输出结构】
${batchProfileStructure(activeProfile)}`,
  ]);
}

function buildBatchPrompt(repos, title, batchIndex, batchCount, profile){
  const normalized = repos.filter(Boolean);
  if(!normalized.length) return "";
  const groupNote = batchCount > 1 ? `\n（当前是第 ${batchIndex}/${batchCount} 组）` : "";
  return buildCollectionPromptText(normalized, title, profile, groupNote);
}

function buildCollectionPrompt(repos, title, profile){
  const normalized = repos.filter(Boolean);
  if(!normalized.length) return "";
  return buildCollectionPromptText(normalized, title, profile, "");
}

function compareLanguageRules(profile){
  const compareSpec = promptProfileSectionConfig(profile, "compare", DEFAULT_COMPARE_PROMPT_CONFIG);
  return buildPromptLanguageRules(compareSpec.language_rules, "common", false);
}

function compareProfileFocus(profile){
  const compareSpec = promptProfileSectionConfig(profile, "compare", DEFAULT_COMPARE_PROMPT_CONFIG);
  return resolvePromptProfileText(compareSpec.focus || DEFAULT_COMPARE_PROMPT_CONFIG.focus);
}

function compareProfileStructure(profile){
  const compareSpec = promptProfileSectionConfig(profile, "compare", DEFAULT_COMPARE_PROMPT_CONFIG);
  return resolvePromptProfileText(compareSpec.structure || DEFAULT_COMPARE_PROMPT_CONFIG.structure);
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
