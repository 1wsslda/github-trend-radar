#!/usr/bin/env python3
from __future__ import annotations

JS = r"""async function openExternalUrl(url){
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
  await openAiPrompts(splitRepoPrompts(repos, panel === DISCOVER_PANEL_KEY ? "当前这批候选项目" : "当前 GitHub 趋势列表"));
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
}"""
