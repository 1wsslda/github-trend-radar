#!/usr/bin/env python3
from __future__ import annotations

import json

HTML_TEMPLATE_PART_1 = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__APP_NAME__</title>
<style>
:root { --bg: #0a0a0a; --bg-soft: #121212; --surface: #121212; --surface-2: #1a1a1a; --border: #2a2a2a; --border-strong: #404040; --text: #ededed; --muted: #888888; --accent: #ffffff; --accent-strong: #ffffff; --green: #10b981; --amber: #d9a441; --danger: #f87171; }
* { box-sizing: border-box; } html, body { height: 100%; } body { margin: 0; color: var(--text); background: var(--bg); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-size: 14px; line-height: 1.6; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; letter-spacing: 0.01em; } button, input, select { font: inherit; } a { color: inherit; text-decoration: none; }
.page { max-width: 1200px; margin: 0 auto; padding: 48px 24px 80px; }
.hero { display: flex; justify-content: space-between; align-items: flex-start; padding: 0 0 40px 0; border-bottom: 1px solid var(--border); margin-bottom: 32px; background: transparent; border-radius: 0; box-shadow: none; } .hero h1 { margin: 0 0 12px 0; font-size: 36px; font-weight: 600; letter-spacing: -0.02em; color: #fff; } .hero p { margin: 0; color: var(--muted); max-width: 640px; font-size: 15px; } .hero-note { text-align: right; color: var(--muted); font-size: 13px; font-family: monospace; } .sub { font-size: 13px; color: var(--muted); }
.toolbar { margin-bottom: 32px; padding: 0; border: none; border-radius: 0; background: transparent; box-shadow: none; display: flex; flex-direction: column; gap: 0; } .row { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap; } .stack, .actions, .filters, .states, .badges, .meta { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; } .stack { flex-direction: column; align-items: flex-start; gap: 4px; } .summary { font-size: 15px; font-weight: 500; color: #fff; }
.action, input, select { min-height: 36px; padding: 0 16px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg); color: var(--text); outline: none; transition: all 0.2s ease; } input[type="checkbox"] { min-height: auto; } input[type="search"] { width: 280px; } .action { cursor: pointer; background: var(--surface-2); font-weight: 500; font-size: 13px; } .action:hover { border-color: var(--border-strong); background: var(--border); color: #fff; transform: none; } .primary { background: #fff; color: #000; border-color: transparent; } .primary:hover { background: #ddd; color: #000; }
.ghost { background: transparent; border-color: transparent; color: var(--muted); padding: 0 8px; } .ghost:hover { background: var(--surface-2); color: var(--text); border-color: transparent; } .danger-hover:hover { color: var(--danger) !important; border-color: var(--danger) !important; background: transparent !important; }
.tabs { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 32px; border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-top: 0; } .tab { padding: 6px 12px; border: none; background: transparent; color: var(--muted); cursor: pointer; font-size: 14px; font-weight: 500; border-radius: 4px; transition: color 0.2s; } .tab:hover { color: var(--text); } .tab.active { color: #fff; background: var(--surface-2); border-color: transparent; }
.cards { display: flex; flex-direction: column; gap: 0; } .card, .update-card, .compare-card { padding: 24px 0; display: grid; gap: 12px; border: none; border-bottom: 1px solid var(--border); background: transparent; box-shadow: none; border-radius: 0; position: relative; transition: all 0.2s; } .card::before, .update-card::before { content: ""; position: absolute; left: -24px; top: 0; bottom: 0; width: 2px; background: #fff; transform: scaleY(0); transition: transform 0.2s ease; transform-origin: center; } .card.selectable:hover::before, .update-card.selectable:hover::before { transform: scaleY(1); } .card.selectable, .update-card.selectable { cursor: pointer; } .card.selected, .update-card.selected { background: var(--surface-2); padding-left: 24px; margin-left: -24px; border-radius: 8px; border-bottom-color: transparent; box-shadow: none; } .card.selected::before, .update-card.selected::before { transform: scaleY(1); left: 0; }
.card .states .action, .update-card .states .action { opacity: 0.4; transition: opacity 0.2s ease; } .card:hover .states .action, .update-card:hover .states .action { opacity: 1; }
.title { color: #fff; text-decoration: none; font-size: 18px; font-weight: 600; letter-spacing: -0.01em; } .title:hover { color: #fff; text-decoration: underline; text-underline-offset: 4px; } .badge { display: inline-flex; align-items: center; gap: 6px; padding: 2px 8px; border-radius: 4px; background: var(--surface-2); color: var(--muted); font-size: 12px; font-family: monospace; border: 1px solid var(--border); } .badge.gain { background: rgba(16, 185, 129, 0.1); border-color: var(--green); color: var(--green); } .badge.source { background: var(--surface); border-style: dashed; } .badge.selected { background: #fff; color: #000; border-color: #fff; }
.state-btn { padding: 4px 12px; border-radius: 4px; border: 1px solid var(--border); background: transparent; color: var(--muted); cursor: pointer; font-size: 12px; } .state-btn:hover { border-color: var(--border-strong); color: var(--text); } .state-btn.active { color: #000; background: #fff; border-color: #fff; font-weight: 500; } .meta { font-size: 13px; color: var(--muted); font-family: monospace; } .empty { padding: 64px 0; border: none; border-radius: 0; background: transparent; text-align: center; color: var(--muted); font-size: 14px; } .notice { padding: 16px; border: 1px solid var(--border-strong); background: var(--surface-2); color: var(--text); font-size: 13px; line-height: 1.6; border-radius: 6px; border-left: 3px solid #fff; }
.toast { position: fixed; right: 24px; bottom: 24px; padding: 16px 20px; border: 1px solid var(--border-strong); background: var(--bg); color: #fff; font-size: 13px; font-weight: 500; opacity: 0; transform: translateY(12px); transition: all 0.2s ease; z-index: 50; box-shadow: 0 24px 48px rgba(0,0,0,0.5); } .toast.show { opacity: 1; transform: translateY(0); }
.overlay { position: fixed; inset: 0; display: none; background: rgba(0,0,0,0.8); backdrop-filter: blur(4px); z-index: 40; overflow-y: auto; padding: 40px 20px; } .overlay.show { display: block; } .panel { margin: 0 auto; border: 1px solid var(--border-strong); background: var(--bg); box-shadow: 0 32px 64px rgba(0,0,0,0.5); border-radius: 12px; } .overlay.settings .panel, .overlay.compare .panel { max-width: 900px; } .overlay.detail .panel { max-width: 600px; margin-right: 40px; margin-left: auto; }
.panel-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; padding: 32px 40px 24px; border-bottom: 1px solid var(--border); } .panel-title { font-size: 24px; font-weight: 600; color: #fff; letter-spacing: -0.02em; margin-bottom: 8px; } .panel-body { padding: 32px 40px 40px; } .detail-grid, .compare-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; } .compare-grid { gap: 32px; } .detail-item { padding: 0; background: transparent; border: none; border-radius: 0; } .detail-item strong { display: block; margin-bottom: 4px; color: var(--muted); font-size: 12px; font-family: monospace; text-transform: uppercase; letter-spacing: 0.05em; } .detail-item span { color: var(--text); font-size: 14px; }
.topic-list { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; } .topic { padding: 4px 10px; border-radius: 4px; background: var(--surface-2); color: var(--muted); font-size: 12px; font-family: monospace; } .link-inline { color: #fff; text-decoration: underline; text-underline-offset: 4px; } .link-inline:hover { color: var(--muted); } .danger { color: #fff; }
@media (max-width: 900px) { .hero { flex-direction: column; gap: 16px; } .hero-note { text-align: left; } .detail-grid, .compare-grid { grid-template-columns: 1fr; } .panel-head, .panel-body { padding: 24px; } .overlay.detail .panel { margin: 0 auto; } }
@media (max-width: 640px) { .page { padding: 24px 16px 40px; } .card::before, .update-card::before { display: none; } .row { flex-direction: column; align-items: stretch; } .actions, .filters { width: 100%; flex-wrap: wrap; } input[type="search"] { width: 100%; } }
</style>
</head>
<body>
<div class="page">
  <section class="hero">
    <div>
      <h1>__APP_NAME__</h1>
      <p>桌面托盘常驻版。趋势榜、收藏、稍后看、已读、更新追踪、仓库详情、仓库对比和 ChatGPT 分析都集中在这里。点击卡片空白处即可直接选中仓库。</p>
      <div class="sub" style="margin-top:10px">本程序不强制要求 VPN；但如果当前网络无法访问 GitHub，请先准备好代理或 VPN，再到“设置”里填写代理地址。</div>
    </div>
    <div style="display:flex; flex-direction:column; align-items:flex-end; gap:12px;">
      <div class="hero-note" id="note"></div>
      <div class="actions" style="gap:4px;">
        <button class="action ghost" onclick="hideToTray()">隐藏托盘</button>
        <button class="action ghost" onclick="exportUserState()">导出数据</button>
        <button class="action ghost" onclick="openSettings()">设置</button>
        <button class="action ghost danger-hover" onclick="exitApp()">退出程序</button>
      </div>
    </div>
  </section>
  <section class="toolbar">
    <div class="row" style="align-items:center;">
      <div class="stack">
        <div class="summary">当前可见 <span id="visible-count">0</span><span id="visible-label"> 仓库</span> · 已选 <span id="selected-count">0</span> 项</div>
      </div>
      <div class="filters">
        <input id="search" type="search" placeholder="搜索仓库 / 描述 / 语言 / 更新...">
        <select id="language"></select>
        <select id="state-filter"><option value="">全部状态</option><option value="unmarked">只看未标记</option><option value="favorites">只看收藏</option><option value="watch_later">只看稍后看</option><option value="read">只看已读</option><option value="ignored">只看忽略</option></select>
        <select id="sort-primary"><option value="stars">总星标</option><option value="trending">GitHub 趋势</option><option value="gained">增长量</option><option value="forks">Fork</option><option value="name">仓库名</option><option value="language">语言</option></select>
        <select id="ai-target"><option value="web">ChatGPT Web</option><option value="desktop">ChatGPT App</option><option value="copy">只复制</option></select>
        <button class="action" onclick="analyzeVisible()">分析列表</button>
        <button class="action" onclick="refreshNow()">刷新</button>
      </div>
    </div>
    <div class="row" id="batch-actions-row" style="display:none; margin-top:16px; padding-top:16px; border-top:1px solid var(--border);">
      <div class="actions">
        <button class="action" onclick="selectVisible()">全选面板</button>
        <button class="action danger-hover" onclick="clearSelected()">清空选择</button>
        <button class="action primary" onclick="analyzeSelected()">批量分析</button>
        <button class="action" onclick="openCompareSelected()">对比已选 (2)</button>
        <button class="action" onclick="batchSetState('favorites')">批量收藏</button>
        <button class="action" onclick="batchSetState('read')">批量已读</button>
        <button class="action" onclick="batchSetState('ignored')">批量忽略</button>
        <button class="action danger-hover" onclick="clearFavoriteUpdates()">清空更新记录</button>
      </div>
    </div>
  </section>
  <div class="tabs" id="tabs"></div>
  <div class="cards" id="cards"></div>
</div>
<div class="toast" id="toast"></div>
<section class="overlay settings" id="settings-modal"><div class="panel"><div class="panel-head"><div><div class="panel-title">设置</div><div class="sub">GitHub Token、代理、刷新间隔、榜单条数、端口和关闭行为都在这里调整。</div></div><button class="action" onclick="closeSettings()">关闭</button></div><div class="panel-body"><div class="filters"><input id="setting-token" type="password" placeholder="GitHub Token"><input id="setting-proxy" type="text" placeholder="代理地址，留空则自动探测"><input id="setting-refresh-hours" type="number" min="1" max="24" placeholder="刷新间隔（小时）"><input id="setting-result-limit" type="number" min="10" max="100" placeholder="榜单条数"><input id="setting-port" type="number" min="1" max="65535" placeholder="端口"><select id="setting-close-behavior"><option value="tray">关闭主窗口时保留托盘运行</option><option value="exit">关闭主窗口时直接退出程序</option></select><label class="action" style="display:flex;align-items:center;gap:8px"><input id="setting-auto-start" type="checkbox">开机启动</label></div><div class="notice" style="margin-top:12px">网络提醒：程序本身不提供 VPN 或翻墙能力。能正常访问 GitHub 时可直接使用；如果趋势列表刷不出来、仓库详情加载失败，通常需要先开启代理或 VPN，然后把代理地址填到上面的“代理地址”里。</div><div class="notice" style="margin-top:12px">关闭提醒：如果选择“保留托盘运行”，主窗口关闭后程序仍会继续运行，图标可能收在任务栏右下角的隐藏图标里。</div><div class="sub" id="settings-runtime-hint" style="margin-top:12px"></div><div class="actions" style="margin-top:16px"><button class="action primary" onclick="saveSettings()">保存设置</button></div></div></div></section>
<section class="overlay detail" id="detail-modal"><div class="panel"><div class="panel-head"><div><div class="panel-title">仓库详情</div><div class="sub" id="detail-title">加载中...</div></div><button class="action" onclick="closeDetail()">关闭</button></div><div class="panel-body" id="detail-body"></div></div></section>
<section class="overlay compare" id="compare-modal"><div class="panel"><div class="panel-head"><div><div class="panel-title">仓库对比</div><div class="sub">对比功能定位、社区热度、近期活跃度和适用场景。</div></div><button class="action" onclick="closeCompare()">关闭</button></div><div class="panel-body" id="compare-body"></div></div></section>
<script>
const INITIAL=__PAYLOAD__;
const UPDATE_PANEL_KEY="favorite-updates";
const INTERACTIVE_SELECTOR="button,a,input,select,label,textarea";
const SORT_KEYS=new Set(["stars","trending","gained","forks","name","language"]);
let snapshot=INITIAL.snapshot||{};
let userState=INITIAL.userState||{};
let settings=INITIAL.settings||{};
let currentNote=INITIAL.note||"";
let panel=localStorage.getItem("gtr-tab")||"daily";
let sortPrimary=normalizeSortKey(localStorage.getItem("gtr-sort-primary")||settings.default_sort||"stars");
let aiTarget=normalizeAiTarget(localStorage.getItem("gtr-ai-target")||"web");
let comparePrompt="";
let selectedUrls=loadSelectedUrls();
let languageFilter=localStorage.getItem("gtr-language")||"";
function normalizeSortKey(value){const key=String(value||"").trim();return SORT_KEYS.has(key)?key:"stars";}
function normalizeAiTarget(value){const key=String(value||"").trim();return ["web","desktop","copy"].includes(key)?key:"web";}
function closeBehaviorLabel(value){return String(value||"").trim()==="exit"?"关闭主窗口时直接退出程序":"关闭主窗口时保留托盘运行";}
function loadSelectedUrls(){try{const raw=JSON.parse(localStorage.getItem("gtr-selected")||"[]");return new Set(Array.isArray(raw)?raw.filter(Boolean):[]);}catch(_err){return new Set();}}
function saveSelectedUrls(){localStorage.setItem("gtr-selected",JSON.stringify([...selectedUrls]));}
function h(value){return String(value??"").replace(/[&<>"']/g,char=>{if(char==="&") return "&amp;";if(char==="<") return "&lt;";if(char===">") return "&gt;";if(char==='"') return "&quot;";return "&#39;";});}
function sleep(ms){return new Promise(resolve=>setTimeout(resolve,ms));}
function toast(message){const node=document.getElementById("toast");node.textContent=message;node.classList.add("show");clearTimeout(window.__toastTimer);window.__toastTimer=setTimeout(()=>node.classList.remove("show"),2400);}
async function copyText(text,label){const value=String(text||"").trim();if(!value){toast("没有可复制的内容");return false;}try{if(navigator.clipboard&&navigator.clipboard.writeText){await navigator.clipboard.writeText(value);}else{throw new Error("clipboard");}}catch(_err){const area=document.createElement("textarea");area.value=value;area.style.position="fixed";area.style.opacity="0";document.body.appendChild(area);area.focus();area.select();document.execCommand("copy");document.body.removeChild(area);}toast(label||"已复制");return true;}
function current(key){return Array.isArray(snapshot[key])?snapshot[key]:[];}
function saved(key){return (userState[key]||[]).map(url=>userState.repo_records?.[url]).filter(Boolean);}
function updateByUrl(url){return (userState.favorite_updates||[]).find(item=>item.url===url)||null;}
function synthesizeRepoFromUpdate(update){if(!update||!String(update.full_name||"").includes("/")) return null;const [owner,name]=String(update.full_name).split("/",2);return {full_name:update.full_name,owner,name,url:update.url,description:"",description_raw:"",language:"",stars:update.stars||0,forks:update.forks||0,gained:0,gained_text:"",growth_source:"unavailable",rank:0,period_key:UPDATE_PANEL_KEY,source_label:"收藏更新"};}
function repoByUrl(url){for(const period of INITIAL.periods||[]){const hit=current(period.key).find(repo=>repo.url===url);if(hit) return hit;}if(userState.repo_records?.[url]) return userState.repo_records[url];return synthesizeRepoFromUpdate(updateByUrl(url));}
function cleanupSelected(){const valid=[...selectedUrls].filter(url=>repoByUrl(url)||updateByUrl(url));if(valid.length!==selectedUrls.size){selectedUrls=new Set(valid);saveSelectedUrls();}}
function selectedRepos(){cleanupSelected();const seen=new Set();return [...selectedUrls].map(url=>repoByUrl(url)).filter(repo=>repo&&!seen.has(repo.url)&&seen.add(repo.url));}
function selectedCount(){cleanupSelected();return selectedUrls.size;}
function growthSource(repo){return String(repo?.growth_source||"").trim();}
function hasGrowthValue(repo){return Number(repo?.gained||0)>0||growthSource(repo)==="trending";}
function gainBadgeClass(repo){return hasGrowthValue(repo)?"gain":"source";}
function gainLabel(repo){const source=growthSource(repo);if(source==="estimated"){return Number(repo?.gained||0)>0?`较上次 +${repo.gained}`:"较上次持平";}if(source==="unavailable"){if(String(repo?.source_label||"").includes("收藏更新")) return "更新追踪项";return "待下次估算";}if(repo.gained_text) return repo.gained_text;if((repo.gained||0)>0) return `+${repo.gained}`;return "暂缺增长数据";}
function repoLine(repo){return `- ${repo.full_name} | ${repo.language||"未知语言"} | Stars ${repo.stars||0} | ${repo.url}\\n  简介: ${repo.description||repo.description_raw||"暂无描述"}`;}
function buildRepoPrompt(repo){return `请用中文分析这个 GitHub 仓库，并按下面结构输出：
1. 这个项目是做什么的
2. 适合哪些用户或场景
3. 技术亮点与差异化
4. 商业化、产品化或副业机会
5. 可能的风险和局限
6. 是否值得持续关注

仓库: ${repo.full_name}
链接: ${repo.url}
语言: ${repo.language||"未知语言"}
总星标: ${repo.stars||0}
增长: ${gainLabel(repo)}
来源: ${repo.source_label||"未知来源"}
简介: ${repo.description||repo.description_raw||"暂无描述"}`;}
function buildBatchPrompt(repos,title,batchIndex,batchCount){const groupNote=batchCount>1?`\\n当前是第 ${batchIndex}/${batchCount} 组。`:"";return `请用中文分别分析下面这些 GitHub 仓库，并对每个仓库分别输出：
1. 项目是做什么的
2. 适合哪些用户或场景
3. 技术亮点
4. 风险和注意点
5. 是否值得持续关注${groupNote}

分析范围: ${title}

仓库列表：
${repos.map(repoLine).join("\\n")}`;}
function splitRepoPrompts(repos,title,maxEncodedLength=2600,maxItemsPerBatch=4){const normalized=repos.filter(Boolean);if(!normalized.length) return [];if(normalized.length===1) return [buildRepoPrompt(normalized[0])];const batches=[];let currentBatch=[];const buildDraft=candidate=>`请用中文分别分析下面这些 GitHub 仓库，并对每个仓库分别输出：1. 项目是做什么的 2. 适合哪些用户或场景 3. 技术亮点 4. 风险和注意点 5. 是否值得持续关注\\n分析范围: ${title}\\n仓库列表：\\n${candidate.map(repoLine).join("\\n")}`;for(const repo of normalized){const candidate=[...currentBatch,repo];const encodedLength=encodeURIComponent(buildDraft(candidate)).length;if(currentBatch.length&&(encodedLength>maxEncodedLength||candidate.length>maxItemsPerBatch)){batches.push(currentBatch);currentBatch=[repo];}else{currentBatch=candidate;}}if(currentBatch.length) batches.push(currentBatch);return batches.map((batch,index)=>buildBatchPrompt(batch,title,index+1,batches.length));}
async function openExternalUrl(url){const target=String(url||"").trim();if(!target) return false;try{const resp=await fetch("/api/open-external",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:target})});const data=await resp.json();if(resp.ok&&data.ok) return true;}catch(_err){}window.open(target,"_blank","noopener");return true;}
async function openChatGPTPrompts(prompts){const queue=prompts.filter(Boolean);if(!queue.length) return false;const mode=normalizeAiTarget(document.getElementById("ai-target")?.value||aiTarget);aiTarget=mode;localStorage.setItem("gtr-ai-target",aiTarget);if(mode==="copy"){await copyText(queue.join("\\n\\n-----\\n\\n"),"分析提示词已复制");return true;}await copyText(queue[queue.length-1],queue.length===1?"分析提示词已复制，正在打开 ChatGPT":`已准备 ${queue.length} 组提示词，正在批量打开 ChatGPT`);for(let index=0;index<queue.length;index+=1){const resp=await fetch("/api/chatgpt/open",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({mode,prompt:queue[index]})});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||"打开 ChatGPT 失败");return false;}if(index<queue.length-1) await sleep(300);}toast(queue.length===1?"已打开 ChatGPT":`已批量打开 ${queue.length} 组 ChatGPT 分析`);return true;}
"""
HTML_TEMPLATE_PART_2 = """function compareByKey(a,b,key){if(key==="trending") return (a.rank||9999)-(b.rank||9999)||(b.gained||0)-(a.gained||0)||(b.stars||0)-(a.stars||0);if(key==="gained") return (b.gained||0)-(a.gained||0)||(b.stars||0)-(a.stars||0)||(a.rank||9999)-(b.rank||9999);if(key==="forks") return (b.forks||0)-(a.forks||0)||(b.stars||0)-(a.stars||0)||(a.rank||9999)-(b.rank||9999);if(key==="name") return String(a.full_name||"").localeCompare(String(b.full_name||""),"zh-Hans-CN")||(a.rank||9999)-(b.rank||9999);if(key==="language") return String(a.language||"").localeCompare(String(b.language||""),"zh-Hans-CN")||(b.stars||0)-(a.stars||0)||(a.rank||9999)-(b.rank||9999);return (b.stars||0)-(a.stars||0)||(b.gained||0)-(a.gained||0)||(a.rank||9999)-(b.rank||9999);}
function visibleRepos(){if(panel===UPDATE_PANEL_KEY) return [];const raw=panel.startsWith("saved:")?saved(panel.split(":")[1]):current(panel);const query=document.getElementById("search").value.trim().toLowerCase();const language=document.getElementById("language").value;const stateFilter=document.getElementById("state-filter").value;const repos=raw.filter(repo=>{const haystack=`${repo.full_name} ${repo.description||""} ${repo.description_raw||""} ${repo.language||""} ${repo.source_label||""}`.toLowerCase();if(query&&!haystack.includes(query)) return false;if(language&&(repo.language||"")!==language) return false;if(stateFilter==="unmarked"){if((INITIAL.states||[]).some(state=>(userState[state.key]||[]).includes(repo.url))) return false;}else if(stateFilter&&!((userState[stateFilter]||[]).includes(repo.url))){return false;}return true;});const sortKeys=[sortPrimary,"trending"].filter((key,index,array)=>key&&array.indexOf(key)===index);repos.sort((a,b)=>{for(const key of sortKeys){const result=compareByKey(a,b,key);if(result) return result;}return 0;});return repos;}
function visibleUpdates(){if(panel!==UPDATE_PANEL_KEY) return [];const query=document.getElementById("search").value.trim().toLowerCase();return (userState.favorite_updates||[]).filter(update=>{const haystack=`${update.full_name||""} ${(update.changes||[]).join(" ")} ${update.latest_release_tag||""}`.toLowerCase();return !query||haystack.includes(query);});}
function visibleLinkList(){return panel===UPDATE_PANEL_KEY?visibleUpdates().map(update=>update.url):visibleRepos().map(repo=>repo.url);}
function tabsData(){return [...(INITIAL.periods||[]).map(period=>({key:period.key,label:period.label,count:current(period.key).length})),...(INITIAL.states||[]).map(state=>({key:`saved:${state.key}`,label:state.label,count:(userState[state.key]||[]).length})),{key:UPDATE_PANEL_KEY,label:"收藏更新",count:(userState.favorite_updates||[]).length}];}
function ensureValidPanel(){const keys=new Set(tabsData().map(tab=>tab.key));if(!keys.has(panel)){panel="daily";localStorage.setItem("gtr-tab",panel);}}
function renderRepoCards(repos){if(!repos.length) return '<div class="empty">当前面板没有匹配结果。</div>';return repos.map(repo=>`<article class="card selectable ${selectedUrls.has(repo.url)?"selected":""}" data-select-url="${h(repo.url)}"><div class="row"><div><a class="title" href="${h(repo.url)}" target="_blank" rel="noopener" data-external-url="${h(repo.url)}">${h(repo.full_name)}</a><div class="badges"><span class="badge ${gainBadgeClass(repo)}">${h(gainLabel(repo))}</span><span class="badge source">${h(repo.source_label||"")}</span>${selectedUrls.has(repo.url)?'<span class="badge selected">已选</span>':""}</div></div><div class="meta">#${repo.rank||"-"}</div></div><div style="color:var(--muted)">${h(repo.description||repo.description_raw||"暂无描述")}</div><div class="meta">Stars ${repo.stars||0} · Fork ${repo.forks||0} · ${h(repo.language||"未知语言")}</div><div class="states">${(INITIAL.states||[]).map(state=>`<button class="state-btn ${(userState[state.key]||[]).includes(repo.url)?"active":""}" onclick='toggleState(${JSON.stringify(state.key)}, ${JSON.stringify(repo.url)})'>${h(state.button)}</button>`).join("")}<button class="action" onclick='analyzeRepo(${JSON.stringify(repo.url)})'>ChatGPT</button><button class="action" onclick='openDetail(${JSON.stringify(repo.owner)}, ${JSON.stringify(repo.name)}, ${JSON.stringify(repo.full_name)})'>详情</button></div></article>`).join("");}
function renderUpdateCards(items){if(!items.length) return '<div class="empty">收藏仓库最近还没有检测到新的变化。</div>';return items.map(update=>`<article class="update-card selectable ${selectedUrls.has(update.url)?"selected":""}" data-select-url="${h(update.url)}"><div class="row"><div><a class="title" href="${h(update.url)}" target="_blank" rel="noopener" data-external-url="${h(update.url)}">${h(update.full_name)}</a><div class="meta">${h(update.checked_at||"未知")}</div></div><div class="badges">${update.latest_release_tag?`<span class="badge source">${h(update.latest_release_tag)}</span>`:""}${selectedUrls.has(update.url)?'<span class="badge selected">已选</span>':""}</div></div><div class="badges">${(update.changes||[]).map(change=>`<span class="badge gain">${h(change)}</span>`).join("")}</div><div class="meta">Stars ${update.stars||0} · Fork ${update.forks||0} · 最近推送 ${h(update.pushed_at||"未知")}</div><div class="states"><button class="action" onclick='analyzeRepo(${JSON.stringify(update.url)})'>ChatGPT</button><button class="action" onclick='openDetailFromRecord(${JSON.stringify(update.full_name)}, ${JSON.stringify(update.url)})'>详情</button></div></article>`).join("");}
function render(){cleanupSelected();ensureValidPanel();const isUpdatePanel=panel===UPDATE_PANEL_KEY;document.getElementById("note").textContent=currentNote;const languages=[...new Set((INITIAL.periods||[]).flatMap(period=>current(period.key).map(repo=>repo.language).filter(Boolean)))].sort((a,b)=>String(a).localeCompare(String(b),"zh-Hans-CN"));const languageNode=document.getElementById("language");languageNode.innerHTML='<option value="">全部语言</option>'+languages.map(language=>`<option value="${h(language)}">${h(language)}</option>`).join("");languageNode.value=languages.includes(languageFilter)?languageFilter:"";languageFilter=languageNode.value;languageNode.disabled=isUpdatePanel;document.getElementById("state-filter").disabled=isUpdatePanel;document.getElementById("tabs").innerHTML=tabsData().map(tab=>`<button class="tab ${tab.key===panel?"active":""}" onclick='setPanel(${JSON.stringify(tab.key)})'>${h(tab.label)} <span style="color:var(--accent)">${tab.count}</span></button>`).join("");const repos=visibleRepos();const updates=visibleUpdates();document.getElementById("visible-count").textContent=isUpdatePanel?updates.length:repos.length;document.getElementById("visible-label").textContent=isUpdatePanel?" 条更新":" 个仓库";document.getElementById("selected-count").textContent=selectedCount();document.getElementById("cards").innerHTML=isUpdatePanel?renderUpdateCards(updates):renderRepoCards(repos);}
function setPanel(nextPanel){panel=String(nextPanel||"daily");localStorage.setItem("gtr-tab",panel);render();}
function toggleSelected(url){if(selectedUrls.has(url)) selectedUrls.delete(url);else selectedUrls.add(url);saveSelectedUrls();render();}
function clearSelected(){if(!selectedUrls.size){toast("当前没有已选条目");return;}selectedUrls.clear();saveSelectedUrls();render();toast("已清空选择");}
function selectVisible(){const urls=visibleLinkList();if(!urls.length){toast(panel===UPDATE_PANEL_KEY?"当前面板没有可选中的更新":"当前面板没有可选中的仓库");return;}urls.forEach(url=>selectedUrls.add(url));saveSelectedUrls();render();toast(`已选中 ${urls.length} 项`);}
async function analyzeRepo(url){const repo=repoByUrl(url);if(!repo){toast("未找到仓库信息");return;}await openChatGPTPrompts([buildRepoPrompt(repo)]);}
async function analyzeVisible(){if(panel===UPDATE_PANEL_KEY){toast("收藏更新面板不支持整页分析");return;}const repos=visibleRepos().slice(0,20);if(!repos.length){toast("当前列表没有可分析的仓库");return;}await openChatGPTPrompts(splitRepoPrompts(repos,"当前 GitHub 趋势列表"));}
async function analyzeSelected(){const repos=selectedRepos();if(!repos.length){toast("请先选中仓库");return;}await openChatGPTPrompts(splitRepoPrompts(repos,"已选仓库"));}
async function fetchRepoDetails(repo){const resp=await fetch(`/api/repo-details?owner=${encodeURIComponent(repo.owner)}&name=${encodeURIComponent(repo.name)}`,{cache:"no-store"});const data=await resp.json();if(!resp.ok||!data.ok) throw new Error(data.error||"详情获取失败");return data.details;}
function buildComparePrompt(a,b,detailA,detailB){return `请用中文对比下面两个 GitHub 仓库，并输出：
1. 两个项目分别解决什么问题
2. 功能定位和差异化对比
3. 社区热度与活跃度对比
4. 各自更适合哪些用户和场景
5. 如果只能长期关注一个，更建议关注哪一个，为什么

项目 A
名称: ${a.full_name}
链接: ${a.url}
语言: ${a.language||"未知语言"}
Stars: ${detailA.stars||a.stars||0}
Forks: ${detailA.forks||a.forks||0}
最近推送: ${detailA.pushed_at||"未知"}
简介: ${detailA.description||detailA.description_raw||a.description||a.description_raw||"暂无描述"}
README 摘要: ${detailA.readme_summary||detailA.readme_summary_raw||"暂无"}

项目 B
名称: ${b.full_name}
链接: ${b.url}
语言: ${b.language||"未知语言"}
Stars: ${detailB.stars||b.stars||0}
Forks: ${detailB.forks||b.forks||0}
最近推送: ${detailB.pushed_at||"未知"}
简介: ${detailB.description||detailB.description_raw||b.description||b.description_raw||"暂无描述"}
README 摘要: ${detailB.readme_summary||detailB.readme_summary_raw||"暂无"}`;}
async function openCompareSelected(){const repos=selectedRepos();if(repos.length!==2){toast("请先选中 2 个仓库再对比");return;}document.getElementById("compare-body").innerHTML='<div class="empty">正在拉取对比数据...</div>';document.getElementById("compare-modal").classList.add("show");try{const [repoA,repoB]=repos;const [detailA,detailB]=await Promise.all([fetchRepoDetails(repoA),fetchRepoDetails(repoB)]);comparePrompt=buildComparePrompt(repoA,repoB,detailA,detailB);document.getElementById("compare-body").innerHTML=`<div class="actions" style="margin-bottom:14px"><button class="action primary" onclick="analyzeCompare()">ChatGPT 对比</button></div><div class="compare-grid">${renderCompareCard(repoA,detailA)}${renderCompareCard(repoB,detailB)}</div>`;}catch(error){comparePrompt="";document.getElementById("compare-body").innerHTML=`<div class="empty">${h(error.message||"对比数据加载失败")}</div>`;}}
function renderCompareCard(repo,detail){return `<article class="compare-card"><div class="title">${h(repo.full_name)}</div><div class="detail-grid"><div class="detail-item"><strong>语言</strong><span>${h(repo.language||"未知语言")}</span></div><div class="detail-item"><strong>License</strong><span>${h(detail.license||"未标注")}</span></div><div class="detail-item"><strong>Stars</strong><span>${detail.stars||repo.stars||0}</span></div><div class="detail-item"><strong>Forks</strong><span>${detail.forks||repo.forks||0}</span></div><div class="detail-item"><strong>最近推送</strong><span>${h(detail.pushed_at||"未知")}</span></div><div class="detail-item"><strong>Open Issues</strong><span>${detail.open_issues||0}</span></div></div><div style="color:var(--muted)">${h(detail.description||detail.description_raw||repo.description||repo.description_raw||"暂无描述")}</div><div style="color:var(--muted)">${h(detail.readme_summary||detail.readme_summary_raw||"暂无 README 摘要")}</div><div class="actions"><a class="action" href="${h(repo.url)}" target="_blank" rel="noopener" data-external-url="${h(repo.url)}">打开 GitHub</a></div></article>`;}
async function analyzeCompare(){if(!comparePrompt){toast("当前没有可分析的对比内容");return;}await openChatGPTPrompts([comparePrompt]);}
async function toggleState(key,url){const repo=repoByUrl(url);if(!repo) return;const resp=await fetch("/api/state",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({state:key,enabled:!((userState[key]||[]).includes(url)),repo})});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||"保存失败");return;}userState=data.user_state;render();}
async function batchSetState(stateKey){const repos=selectedRepos();if(!repos.length){toast("请先选中仓库再批量操作");return;}let lastState=null;for(const repo of repos){const resp=await fetch("/api/state",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({state:stateKey,enabled:true,repo})});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||"批量操作失败");return;}if(data.user_state) lastState=data.user_state;}if(lastState) userState=lastState;render();const label=(INITIAL.states||[]).find(state=>state.key===stateKey)?.label||stateKey;toast(`已将 ${repos.length} 个仓库加入“${label}”`);}
async function clearFavoriteUpdates(){if(!(userState.favorite_updates||[]).length){toast("当前没有收藏更新记录");return;}if(!window.confirm("确认清空收藏更新记录吗？")) return;const resp=await fetch("/api/favorite-updates/clear",{method:"POST"});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||"清空失败");return;}userState=data.user_state;render();toast(data.message||"已清空收藏更新记录");}
async function refreshNow(){const resp=await fetch("/api/refresh",{method:"POST"});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||"刷新失败");return;}currentNote=data.message||"已开始后台刷新。";render();poll();}
function poll(){clearInterval(window.__pollTimer);window.__pollTimer=setInterval(async()=>{const resp=await fetch("/api/status?ts="+Date.now(),{cache:"no-store"});const data=await resp.json();currentNote=data.refreshing?"后台刷新中...":(data.error||"已显示最新数据");document.getElementById("note").textContent=currentNote;if(!data.refreshing){clearInterval(window.__pollTimer);location.reload();}},1500);}
async function hideToTray(){const resp=await fetch("/api/window/hide",{method:"POST"});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||data.message||"隐藏到托盘失败");return;}toast(data.message||"已隐藏到系统托盘");setTimeout(()=>window.close(),150);}
async function exitApp(){if(!window.confirm("确认直接退出 GitHub Trend Radar 吗？")) return;const resp=await fetch("/api/window/exit",{method:"POST"});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||data.message||"退出程序失败");return;}toast(data.message||"正在退出程序");setTimeout(()=>window.close(),150);}
async function openSettings(){try{const resp=await fetch("/api/settings",{cache:"no-store"});const data=await resp.json();if(resp.ok) settings=data;}catch(_err){}document.getElementById("setting-token").value=settings.github_token||"";document.getElementById("setting-proxy").value=settings.proxy||"";document.getElementById("setting-refresh-hours").value=settings.refresh_hours||1;document.getElementById("setting-result-limit").value=settings.result_limit||25;document.getElementById("setting-port").value=settings.port||8080;document.getElementById("setting-close-behavior").value=settings.close_behavior||"tray";document.getElementById("setting-auto-start").checked=!!settings.auto_start;document.getElementById("settings-runtime-hint").textContent=`当前生效端口 ${settings.effective_port||settings.port||8080} · 当前代理 ${settings.effective_proxy||"未启用"} · 当前关闭行为 ${closeBehaviorLabel(settings.close_behavior)} · 程序不提供 VPN${settings.restart_required?" · 修改端口后需重启生效":""}`;document.getElementById("settings-modal").classList.add("show");}
function closeSettings(){document.getElementById("settings-modal").classList.remove("show");}
async function saveSettings(){const payload={github_token:document.getElementById("setting-token").value,proxy:document.getElementById("setting-proxy").value,refresh_hours:Number(document.getElementById("setting-refresh-hours").value||1),result_limit:Number(document.getElementById("setting-result-limit").value||25),port:Number(document.getElementById("setting-port").value||8080),close_behavior:document.getElementById("setting-close-behavior").value,auto_start:document.getElementById("setting-auto-start").checked,default_sort:sortPrimary};const resp=await fetch("/api/settings",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||"保存失败");return;}settings=data.settings;toast(data.message||"设置已保存");closeSettings();}
"""
HTML_TEMPLATE_PART_3 = """async function openDetail(owner,name,label){document.getElementById("detail-modal").classList.add("show");document.getElementById("detail-title").textContent=label;document.getElementById("detail-body").innerHTML='<div class="empty">正在拉取仓库详情...</div>';try{const detail=await fetchRepoDetails({owner,name});const topics=Array.isArray(detail.topics)?detail.topics.filter(Boolean):[];document.getElementById("detail-body").innerHTML=`<div class="detail-grid"><div class="detail-item"><strong>仓库</strong><span>${h(detail.full_name||label)}</span></div><div class="detail-item"><strong>License</strong><span>${h(detail.license||"未标注")}</span></div><div class="detail-item"><strong>最近推送</strong><span>${h(detail.pushed_at||"未知")}</span></div><div class="detail-item"><strong>最后更新</strong><span>${h(detail.updated_at||"未知")}</span></div><div class="detail-item"><strong>默认分支</strong><span>${h(detail.default_branch||"未知")}</span></div><div class="detail-item"><strong>主页</strong><span>${detail.homepage?`<a class="link-inline" href="${h(detail.homepage)}" target="_blank" rel="noopener" data-external-url="${h(detail.homepage)}">${h(detail.homepage)}</a>`:"未填写"}</span></div></div><div style="margin-top:14px;color:var(--muted)">${h(detail.description||detail.description_raw||"暂无简介")}</div><div style="margin-top:12px;color:var(--muted)">${h(detail.readme_summary||detail.readme_summary_raw||"暂无 README 摘要")}</div><div class="meta" style="margin-top:12px">Stars ${detail.stars||0} · Fork ${detail.forks||0} · Watchers ${detail.watchers||0} · Issues ${detail.open_issues||0}</div>${topics.length?`<div class="topic-list">${topics.map(topic=>`<span class="topic">${h(topic)}</span>`).join("")}</div>`:""}<div class="actions" style="margin-top:16px"><a class="action primary" href="${h(detail.html_url||"#")}" target="_blank" rel="noopener" data-external-url="${h(detail.html_url||"#")}">打开 GitHub</a></div>`;}catch(error){document.getElementById("detail-body").innerHTML=`<div class="empty">${h(error.message||"详情获取失败")}</div>`;}}
function openDetailFromRecord(fullName,url){const repo=repoByUrl(url)||(()=>{const parts=String(fullName||"").split("/");return {full_name:fullName,owner:parts[0]||"",name:parts[1]||""};})();if(!repo.owner||!repo.name){toast("缺少仓库标识");return;}openDetail(repo.owner,repo.name,repo.full_name||fullName);}
function closeDetail(){document.getElementById("detail-modal").classList.remove("show");}
function closeCompare(){document.getElementById("compare-modal").classList.remove("show");}
document.getElementById("cards").addEventListener("click",event=>{if(event.target.closest(INTERACTIVE_SELECTOR)||event.target.closest("[data-external-url]")) return;const card=event.target.closest("[data-select-url]");if(!card) return;toggleSelected(card.getAttribute("data-select-url"));});
document.addEventListener("click",event=>{const target=event.target.closest("[data-external-url]");if(!target) return;event.preventDefault();event.stopPropagation();openExternalUrl(target.getAttribute("data-external-url"));});
document.getElementById("search").value=localStorage.getItem("gtr-search")||"";document.getElementById("state-filter").value=localStorage.getItem("gtr-state-filter")||"";
document.getElementById("search").addEventListener("input",event=>{localStorage.setItem("gtr-search",event.target.value);render();});
document.getElementById("language").addEventListener("change",event=>{languageFilter=event.target.value;localStorage.setItem("gtr-language",languageFilter);render();});
document.getElementById("state-filter").addEventListener("change",event=>{localStorage.setItem("gtr-state-filter",event.target.value);render();});
document.getElementById("sort-primary").value=sortPrimary;
document.getElementById("ai-target").value=aiTarget;
document.getElementById("sort-primary").addEventListener("change",event=>{sortPrimary=normalizeSortKey(event.target.value);localStorage.setItem("gtr-sort-primary",sortPrimary);render();});
document.getElementById("ai-target").addEventListener("change",event=>{aiTarget=normalizeAiTarget(event.target.value);localStorage.setItem("gtr-ai-target",aiTarget);});
document.getElementById("settings-modal").addEventListener("click",event=>{if(event.target.id==="settings-modal") closeSettings();});
document.getElementById("detail-modal").addEventListener("click",event=>{if(event.target.id==="detail-modal") closeDetail();});
document.getElementById("compare-modal").addEventListener("click",event=>{if(event.target.id==="compare-modal") closeCompare();});
window.addEventListener("keydown",event=>{if(event.key!=="Escape") return;closeSettings();closeDetail();closeCompare();});
render();
if(INITIAL.pending) poll();
</script>
</body>
</html>
"""


def build_html(
    *,
    app_name: str,
    snapshot: dict[str, object],
    user_state: dict[str, object],
    settings: dict[str, object],
    periods: list[dict[str, object]],
    states: list[dict[str, object]],
    note: str,
    pending: bool,
) -> str:
    payload = json.dumps(
        {
            "snapshot": snapshot,
            "userState": user_state,
            "settings": settings,
            "periods": periods,
            "states": states,
            "note": note,
            "pending": pending,
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")
    template = HTML_TEMPLATE_PART_1 + HTML_TEMPLATE_PART_2 + HTML_TEMPLATE_PART_3
    return template.replace("__APP_NAME__", app_name).replace("__PAYLOAD__", payload)
