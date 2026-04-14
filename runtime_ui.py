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
:root{
  --font-sans:"Inter",-apple-system,BlinkMacSystemFont,"HarmonyOS Sans SC","MiSans","PingFang SC","Microsoft YaHei",sans-serif;
  --font-mono:"JetBrains Mono","Maple Mono","Fira Code",monospace;
  --bg:#0f0e0b;
  --bg-soft:#171511;
  --surface:#1a1814;
  --surface-2:#211d17;
  --surface-3:#2a241d;
  --border:rgba(232,214,184,.12);
  --border-strong:rgba(245,228,198,.28);
  --text:#f3ede2;
  --text-soft:#ddd2c1;
  --muted:#a99a83;
  --muted-soft:#867763;
  --accent:#e9c98f;
  --accent-strong:#f6deae;
  --accent-ink:#1a1308;
  --green:#7fd0a0;
  --amber:#d8af67;
  --danger:#f49a8d;
  --shadow:0 32px 80px rgba(0,0,0,.34);
}
*{box-sizing:border-box}
html,body{height:100%}
body{
  margin:0;
  color:var(--text);
  background:
    radial-gradient(circle at top, rgba(234,204,145,.08), transparent 0 34%),
    radial-gradient(circle at 20% 15%, rgba(120,102,72,.16), transparent 0 28%),
    linear-gradient(180deg,#0c0b09 0%,#100f0c 38%,#12100d 100%);
  font-family:var(--font-sans);
  font-size:15px;
  line-height:1.7;
  text-rendering:optimizeLegibility;
  font-kerning:normal;
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
}
button,input,select{font:inherit}
a{color:inherit;text-decoration:none}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
::selection{background:rgba(233,201,143,.22);color:var(--text)}

.page{max-width:1360px;margin:0 auto;padding:clamp(28px,5vw,56px) clamp(18px,3vw,32px) 96px}
.hero{display:grid;grid-template-columns:minmax(0,1fr) minmax(280px,340px);gap:32px;align-items:start;margin-bottom:26px}
.hero-copy{position:relative;padding:clamp(28px,4vw,40px);border:1px solid var(--border);border-radius:28px;background:linear-gradient(180deg, rgba(38,33,26,.92), rgba(20,18,14,.94)),radial-gradient(circle at top left, rgba(233,201,143,.12), transparent 0 45%);box-shadow:var(--shadow)}
.hero-copy::after{content:"";position:absolute;inset:1px;border-radius:27px;pointer-events:none;background:linear-gradient(135deg, rgba(255,255,255,.04), transparent 35%, rgba(255,255,255,.01))}
.hero-kicker,.hero-note,.badge,.meta,.meta-pill,.topic,.detail-item strong,.detail-item span,.state-btn,.tab-count{font-family:var(--font-mono);font-variant-numeric:tabular-nums;font-variant-ligatures:contextual}
.hero-kicker{display:inline-flex;align-items:center;gap:10px;margin-bottom:18px;color:var(--accent);font-size:11px;letter-spacing:.18em;text-transform:uppercase}
.hero-kicker::before{content:"";width:28px;height:1px;background:linear-gradient(90deg, rgba(233,201,143,.1), rgba(233,201,143,.8))}
.hero h1{margin:0 0 14px;font-size:clamp(2.4rem,5vw,4.6rem);line-height:1.02;letter-spacing:-.05em;font-weight:680;color:var(--text)}
.hero p{margin:0;max-width:72ch;color:var(--text-soft);font-size:1.04rem}
.hero-support{margin-top:16px;color:var(--muted)}
.hero-rail{display:grid;gap:16px}
.hero-status,.hero-actions{padding:20px 22px;border:1px solid var(--border);border-radius:22px;background:linear-gradient(180deg, rgba(29,26,21,.84), rgba(18,16,13,.92));box-shadow:var(--shadow)}
.hero-status-label{margin-bottom:10px;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.14em}
.hero-note{color:var(--text-soft);font-size:13px;line-height:1.65}
.hero-actions .actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}

.toolbar{margin-bottom:20px;display:grid;gap:14px}
.control-shell,.selection-bar{border:1px solid var(--border);border-radius:24px;background:linear-gradient(180deg, rgba(28,25,20,.9), rgba(20,18,14,.94));box-shadow:var(--shadow)}
.control-shell{display:grid;grid-template-columns:minmax(0,1.08fr) minmax(0,1.5fr);gap:16px 18px;padding:22px 24px}
.toolbar-copy{display:grid;gap:8px;align-content:start}
.summary{font-size:1rem;font-weight:650;line-height:1.35;color:var(--text)}
.sub{color:var(--muted);font-size:.88rem;line-height:1.7}
.toolbar-controls{display:grid;gap:12px}
.filters,.actions,.states,.badges,.meta,.panel-actions,.settings-actions{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.filters{display:grid;grid-template-columns:minmax(220px,1.45fr) repeat(4,minmax(120px,.8fr));gap:10px}
.actions{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.selection-bar{display:none;padding:16px 18px}
.selection-bar.show{display:block}
.selection-title{margin-bottom:10px;color:var(--muted);font-size:12px;letter-spacing:.12em;text-transform:uppercase}

.action,input,select{min-height:44px;width:100%;padding:0 14px;border-radius:14px;border:1px solid var(--border);background:rgba(17,15,12,.88);color:var(--text);transition:border-color .22s ease,background .22s ease,transform .22s ease,box-shadow .22s ease,opacity .22s ease}
input::placeholder{color:var(--muted-soft)}
select{appearance:none;background-image:linear-gradient(45deg, transparent 50%, var(--muted) 50%),linear-gradient(135deg, var(--muted) 50%, transparent 50%);background-position:calc(100% - 18px) calc(50% - 1px),calc(100% - 12px) calc(50% - 1px);background-size:6px 6px,6px 6px;background-repeat:no-repeat}
.action{cursor:pointer;justify-content:center;display:inline-flex;align-items:center;border-color:rgba(233,201,143,.12);background:linear-gradient(180deg, rgba(39,34,27,.86), rgba(22,19,15,.96));color:var(--text-soft);font-weight:560}
.action:hover{transform:translateY(-1px);border-color:rgba(233,201,143,.26);background:linear-gradient(180deg, rgba(48,42,33,.96), rgba(25,21,17,.98));color:var(--text)}
.primary{border-color:rgba(246,222,174,.18);background:linear-gradient(180deg, var(--accent-strong), #dcb778);color:var(--accent-ink)}
.primary:hover{color:var(--accent-ink);background:linear-gradient(180deg, #fae7c2, #e3c286)}
.ghost{background:rgba(17,15,12,.45);color:var(--muted)}
.ghost:hover{color:var(--text-soft)}
.danger-hover:hover{color:var(--danger)!important;border-color:rgba(244,154,141,.34)!important}

.tabs{position:sticky;top:16px;z-index:15;display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:22px;padding:12px;border:1px solid var(--border);border-radius:22px;background:rgba(16,14,11,.84);backdrop-filter:blur(14px);box-shadow:var(--shadow)}
.tab{display:inline-flex;align-items:center;gap:8px;min-height:42px;padding:0 16px;border:none;border-radius:999px;background:transparent;color:var(--muted);cursor:pointer;font-size:.94rem;font-weight:560;transition:background .22s ease,color .22s ease,transform .22s ease}
.tab:hover{color:var(--text);background:rgba(255,255,255,.035)}
.tab.active{background:linear-gradient(180deg, rgba(233,201,143,.18), rgba(233,201,143,.09));color:var(--text)}
.tab-count{color:var(--accent);font-size:.84rem}

.cards{display:grid;gap:16px}
.card,.update-card,.compare-card{position:relative;display:grid;gap:16px;padding:24px 32px;border-radius:18px;border:1px solid rgba(233,214,184,.1);background:radial-gradient(circle at top right, rgba(233,201,143,.07), transparent 0 28%),linear-gradient(180deg, rgba(34,30,24,.96), rgba(24,21,17,.98));box-shadow:var(--shadow);overflow:hidden;transition:border-color .24s ease,box-shadow .24s ease,transform .24s ease}
.card::before,.update-card::before,.compare-card::before{content:"";position:absolute;inset:0;background:linear-gradient(120deg, rgba(255,255,255,.045), transparent 26%, transparent 70%, rgba(255,255,255,.015));pointer-events:none}
.card.selectable,.update-card.selectable{cursor:pointer}
.card.selectable:hover,.update-card.selectable:hover{transform:translateY(-1px);border-color:rgba(245,228,198,.18)}
.card.selected,.update-card.selected{border-color:rgba(233,201,143,.42);box-shadow:0 0 0 1px rgba(233,201,143,.24) inset,0 0 0 10px rgba(233,201,143,.02),var(--shadow)}
.selection-mark{position:absolute;top:18px;right:18px;display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;border:1px solid rgba(233,201,143,.26);background:rgba(233,201,143,.12);color:var(--accent-strong);font-size:11px;letter-spacing:.12em;text-transform:uppercase}
.selection-mark::before{content:"";width:8px;height:8px;border-radius:999px;background:var(--accent);box-shadow:0 0 0 6px rgba(233,201,143,.08)}
.card-head{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:18px;align-items:start}
.card-body{display:grid;gap:14px}
.title{display:block;margin:8px 0 0;color:var(--text);font-size:20px;line-height:1.18;letter-spacing:-.03em;font-weight:700}
.title:hover{color:var(--accent-strong);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:4px}
.desc{max-width:72ch;color:var(--text-soft);font-size:1rem;line-height:1.7}
.desc.muted{color:var(--muted)}
.badges{gap:8px}
.badge{display:inline-flex;align-items:center;gap:6px;min-height:28px;padding:0 10px;border-radius:999px;border:1px solid rgba(233,214,184,.12);background:rgba(15,13,10,.55);color:var(--muted);font-size:.77rem;letter-spacing:.02em}
.badge.gain{color:var(--green);border-color:rgba(127,208,160,.26);background:rgba(127,208,160,.08)}
.badge.source{color:var(--amber);border-color:rgba(216,175,103,.16);background:rgba(216,175,103,.06)}
.badge.selected{color:var(--accent-ink);border-color:rgba(246,222,174,.22);background:var(--accent-strong)}
.meta{gap:8px;color:var(--muted-soft);font-size:.83rem}
.meta-rank{justify-self:end;align-self:start;padding-top:2px;color:rgba(233,201,143,.58)}
.meta-line{display:flex;gap:8px;flex-wrap:wrap;color:var(--muted-soft)}
.meta-pill{display:inline-flex;align-items:center;gap:8px;min-height:32px;padding:0 12px;border-radius:999px;border:1px solid rgba(233,214,184,.08);background:rgba(10,9,7,.36)}
.meta-pill strong{color:var(--muted);font-weight:500}
.states{opacity:.03;pointer-events:none;transform:translateY(6px);transition:opacity .26s ease,transform .26s ease}
.card:hover .states,.update-card:hover .states,.card:focus-within .states,.update-card:focus-within .states,.card.selected .states,.update-card.selected .states{opacity:1;pointer-events:auto;transform:translateY(0)}
.state-btn{min-height:34px;padding:0 12px;border-radius:999px;border:1px solid rgba(233,214,184,.12);background:rgba(11,10,8,.48);color:var(--muted);cursor:pointer;font-size:.8rem;transition:border-color .22s ease,background .22s ease,color .22s ease}
.state-btn:hover{border-color:rgba(233,214,184,.24);color:var(--text-soft)}
.state-btn.active{color:var(--accent-ink);background:var(--accent);border-color:rgba(233,201,143,.3);box-shadow:0 8px 20px rgba(233,201,143,.12)}
.empty{padding:84px 20px;border:1px dashed rgba(233,214,184,.12);border-radius:22px;background:rgba(16,14,11,.62);color:var(--muted);text-align:center;font-size:.95rem}
.notice{padding:16px 18px;border-radius:16px;border:1px solid rgba(233,201,143,.12);background:rgba(18,16,13,.84);color:var(--text-soft);font-size:.9rem;line-height:1.75}
.toast{position:fixed;right:22px;bottom:22px;max-width:min(420px,calc(100vw - 32px));padding:14px 16px;border-radius:16px;border:1px solid rgba(233,201,143,.18);background:rgba(20,17,13,.96);color:var(--text);box-shadow:var(--shadow);opacity:0;transform:translateY(10px);transition:opacity .22s ease,transform .22s ease;pointer-events:none;z-index:60}
.toast.show{opacity:1;transform:translateY(0)}

.overlay{position:fixed;inset:0;opacity:0;visibility:hidden;background:rgba(6,5,4,.58);backdrop-filter:blur(8px);z-index:50;transition:opacity .28s ease,visibility .28s ease}
.overlay.show{opacity:1;visibility:visible}
.panel{position:absolute;top:0;right:0;bottom:0;width:min(620px,100vw);background:radial-gradient(circle at top, rgba(233,201,143,.08), transparent 0 26%),linear-gradient(180deg, rgba(20,17,13,.98), rgba(14,12,10,1));border-left:1px solid rgba(233,214,184,.12);box-shadow:-30px 0 72px rgba(0,0,0,.44);display:flex;flex-direction:column;transform:translateX(100%);transition:transform .34s cubic-bezier(.22,1,.36,1)}
.overlay.show .panel{transform:translateX(0)}
.overlay.compare .panel{width:min(760px,100vw)}
.overlay.settings .panel{width:min(560px,100vw)}
.panel-head{padding:28px 28px 20px;border-bottom:1px solid rgba(233,214,184,.1);display:grid;grid-template-columns:minmax(0,1fr) auto;gap:16px;align-items:start}
.panel-title{margin:0 0 8px;font-size:1.56rem;line-height:1.1;letter-spacing:-.03em;font-weight:700;color:var(--text)}
.panel-body{padding:24px 28px 34px;overflow-y:auto;display:grid;gap:18px}
.settings-grid{display:grid;gap:12px}
.settings-grid .filters{grid-template-columns:1fr}
.settings-grid label.action{justify-content:flex-start}
.detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.compare-grid{display:grid;grid-template-columns:1fr;gap:16px}
.detail-item{padding:14px 15px;border-radius:16px;border:1px solid rgba(233,214,184,.08);background:rgba(24,21,17,.78)}
.detail-item strong{display:block;margin-bottom:8px;color:var(--muted);font-size:.75rem;letter-spacing:.12em;text-transform:uppercase}
.detail-item span{color:var(--text-soft);font-size:.9rem;line-height:1.6}
.topic-list{display:flex;gap:8px;flex-wrap:wrap}
.topic{display:inline-flex;align-items:center;min-height:28px;padding:0 10px;border-radius:999px;background:rgba(233,201,143,.09);border:1px solid rgba(233,201,143,.12);color:var(--accent);font-size:.78rem}
.link-inline{color:var(--accent-strong);text-decoration:underline;text-underline-offset:3px}
.link-inline:hover{color:var(--text)}
.danger{color:var(--danger)}

@media (max-width:1120px){
  .hero,.control-shell{grid-template-columns:1fr}
  .hero-rail{grid-template-columns:1fr 1fr}
  .filters{grid-template-columns:repeat(2,minmax(0,1fr))}
  .actions{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media (max-width:780px){
  .page{padding:20px 14px 72px}
  .hero-copy,.hero-status,.hero-actions,.control-shell,.selection-bar,.tabs{border-radius:20px}
  .hero-rail{grid-template-columns:1fr}
  .actions,.filters{grid-template-columns:1fr}
  .card,.update-card,.compare-card{padding:22px 20px}
  .card-head{grid-template-columns:1fr}
  .meta-rank{justify-self:start}
  .detail-grid{grid-template-columns:1fr}
  .panel-head,.panel-body{padding-left:20px;padding-right:20px}
}
@media (prefers-reduced-motion:reduce){
  *,
  *::before,
  *::after{
    animation:none!important;
    transition:none!important;
    scroll-behavior:auto!important;
  }
}
</style>
</head>
<body>
<div class="page">
  <section class="hero">
    <div class="hero-copy">
      <div class="hero-kicker">Curated GitHub Intelligence</div>
      <h1>__APP_NAME__</h1>
      <p>把 GitHub 趋势、收藏追踪、仓库详情、对比判断和 ChatGPT 分析收进一个更适合长时间阅读与筛选的桌面阅读台。</p>
      <p class="hero-support">像读一份被持续更新的技术选题笔记，而不是在密集工具栏和碎片化卡片之间来回跳转。点击卡片空白处即可直接选中仓库。</p>
    </div>
    <aside class="hero-rail">
      <div class="hero-status">
        <div class="hero-status-label">Runtime</div>
        <div class="hero-note" id="note"></div>
      </div>
      <div class="hero-actions">
        <div class="hero-status-label">Workspace</div>
        <div class="actions">
          <button class="action ghost" onclick="hideToTray()">隐藏到托盘</button>
          <button class="action ghost" onclick="exportUserState()">导出数据</button>
          <button class="action ghost" onclick="openSettings()">设置</button>
          <button class="action ghost danger-hover" onclick="exitApp()">退出程序</button>
        </div>
      </div>
    </aside>
  </section>

  <section class="toolbar">
    <div class="control-shell">
      <div class="toolbar-copy">
        <div class="summary">当前面板可见 <span id="visible-count">0</span><span id="visible-label"> 个仓库</span> · 已选 <span id="selected-count">0</span> 项</div>
        <div class="sub">这是一个偏“读”和“筛”的视图。项目名称和描述是第一焦点，Stars / Fork / 来源等次级信息会被自然后移。仓库链接会使用系统默认浏览器打开，沿用你当前登录态。</div>
        <div class="sub">本程序不强制要求 VPN；如果当前网络无法访问 GitHub，请先准备好代理或 VPN，再到“设置”里填写代理地址。</div>
      </div>
      <div class="toolbar-controls">
        <div class="filters">
          <input id="search" type="search" placeholder="搜索仓库 / 描述 / 语言 / 更新内容">
          <select id="language"></select>
          <select id="state-filter"><option value="">全部状态</option><option value="unmarked">只看未标记</option><option value="favorites">只看收藏</option><option value="watch_later">只看稍后看</option><option value="read">只看已读</option><option value="ignored">只看忽略</option></select>
          <select id="sort-primary"><option value="stars">按总星标排序</option><option value="trending">按 GitHub 趋势排序</option><option value="gained">按增长排序</option><option value="forks">按 Fork 排序</option><option value="name">按仓库名排序</option><option value="language">按语言排序</option></select>
          <select id="ai-target"><option value="web">ChatGPT 网页版</option><option value="desktop">ChatGPT 桌面版</option><option value="copy">仅复制提示词</option></select>
        </div>
        <div class="actions">
          <button class="action" onclick="analyzeVisible()">分析当前列表</button>
          <button class="action" onclick="refreshNow()">立即刷新</button>
          <button class="action" onclick="selectVisible()">全选当前面板</button>
          <button class="action" onclick="clearFavoriteUpdates()">清空更新记录</button>
        </div>
      </div>
    </div>

    <div class="selection-bar" id="batch-actions-row">
      <div class="selection-title" id="selection-title">Selected Repositories</div>
      <div class="actions">
        <button class="action danger-hover" onclick="clearSelected()">清空已选</button>
        <button class="action primary" onclick="analyzeSelected()">批量分析已选</button>
        <button class="action" onclick="openCompareSelected()">对比已选 2 个仓库</button>
        <button class="action" onclick="batchSetState('favorites')">批量收藏</button>
        <button class="action" onclick="batchSetState('read')">批量已读</button>
        <button class="action" onclick="batchSetState('ignored')">批量忽略</button>
        <button class="action" onclick="batchSetState('watch_later')">批量稍后看</button>
        <button class="action" onclick="selectVisible()">重新全选本页</button>
      </div>
    </div>
  </section>

  <div class="tabs" id="tabs"></div>
  <div class="cards" id="cards"></div>
</div>
<div class="toast" id="toast"></div>
<section class="overlay settings" id="settings-modal">
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="panel-title">设置</div>
        <div class="sub">配置 GitHub Token、代理、刷新间隔、榜单条数、端口和关闭行为。</div>
      </div>
      <button class="action" onclick="closeSettings()">关闭</button>
    </div>
    <div class="panel-body settings-grid">
      <div class="filters">
        <input id="setting-token" type="password" placeholder="GitHub Token">
        <input id="setting-proxy" type="text" placeholder="代理地址，留空则自动探测">
        <input id="setting-refresh-hours" type="number" min="1" max="24" placeholder="刷新间隔（小时）">
        <input id="setting-result-limit" type="number" min="10" max="100" placeholder="榜单条数">
        <input id="setting-port" type="number" min="1" max="65535" placeholder="端口">
        <select id="setting-close-behavior"><option value="tray">关闭主窗口时保留托盘运行</option><option value="exit">关闭主窗口时直接退出程序</option></select>
        <label class="action"><input id="setting-auto-start" type="checkbox"> 开机启动</label>
      </div>
      <div class="notice">网络提醒：程序本身不提供 VPN 或翻墙能力。能正常访问 GitHub 时可直接使用；如果趋势列表刷不出来、仓库详情加载失败，通常需要先开启代理或 VPN，然后把代理地址填到上面的“代理地址”里。</div>
      <div class="notice">关闭提醒：如果选择“保留托盘运行”，主窗口关闭后程序仍会继续运行，图标可能收在任务栏右下角的隐藏图标里。</div>
      <div class="sub" id="settings-runtime-hint"></div>
      <div class="settings-actions">
        <button class="action primary" onclick="saveSettings()">保存设置</button>
      </div>
    </div>
  </div>
</section>
<section class="overlay detail" id="detail-modal">
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="panel-title">仓库详情</div>
        <div class="sub" id="detail-title">加载中...</div>
      </div>
      <button class="action" onclick="closeDetail()">关闭</button>
    </div>
    <div class="panel-body" id="detail-body"></div>
  </div>
</section>
<section class="overlay compare" id="compare-modal">
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="panel-title">仓库对比</div>
        <div class="sub">更像在右侧展开一页比对札记，而不是打断阅读流的居中弹窗。</div>
      </div>
      <button class="action" onclick="closeCompare()">关闭</button>
    </div>
    <div class="panel-body" id="compare-body"></div>
  </div>
</section>
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
function renderRepoCards(repos){
  if(!repos.length) return '<div class="empty">当前面板没有匹配结果。</div>';
  return repos.map(repo=>{
    const selected=selectedUrls.has(repo.url);
    const description=h(repo.description||repo.description_raw||"暂无描述");
    return `<article class="card selectable ${selected?"selected":""}" data-select-url="${h(repo.url)}">
      ${selected?'<div class="selection-mark">已选中</div>':""}
      <div class="card-head">
        <div>
          <div class="badges">
            <span class="badge ${gainBadgeClass(repo)}">${h(gainLabel(repo))}</span>
            <span class="badge source">${h(repo.source_label||"GitHub 来源")}</span>
          </div>
          <a class="title" href="${h(repo.url)}" target="_blank" rel="noopener" data-external-url="${h(repo.url)}">${h(repo.full_name)}</a>
        </div>
        <div class="meta meta-rank">#${repo.rank||"-"}</div>
      </div>
      <div class="card-body">
        <div class="desc">${description}</div>
        <div class="meta-line">
          <span class="meta-pill"><strong>Stars</strong><span>${repo.stars||0}</span></span>
          <span class="meta-pill"><strong>Forks</strong><span>${repo.forks||0}</span></span>
          <span class="meta-pill"><strong>Language</strong><span>${h(repo.language||"未知语言")}</span></span>
        </div>
        <div class="states">
          ${(INITIAL.states||[]).map(state=>`<button class="state-btn ${(userState[state.key]||[]).includes(repo.url)?"active":""}" onclick='toggleState(${JSON.stringify(state.key)}, ${JSON.stringify(repo.url)})'>${h(state.button)}</button>`).join("")}
          <button class="action" onclick='analyzeRepo(${JSON.stringify(repo.url)})'>ChatGPT</button>
          <button class="action" onclick='openDetail(${JSON.stringify(repo.owner)}, ${JSON.stringify(repo.name)}, ${JSON.stringify(repo.full_name)})'>详情</button>
        </div>
      </div>
    </article>`;
  }).join("");
}
function renderUpdateCards(items){
  if(!items.length) return '<div class="empty">收藏仓库最近还没有检测到新的变化。</div>';
  return items.map(update=>{
    const selected=selectedUrls.has(update.url);
    const changeBadges=(update.changes||[]).map(change=>`<span class="badge gain">${h(change)}</span>`).join("");
    const summary=(update.changes||[]).length?(update.changes||[]).join(" · "):"最近一次检测没有整理出可展示的变化摘要。";
    return `<article class="update-card selectable ${selected?"selected":""}" data-select-url="${h(update.url)}">
      ${selected?'<div class="selection-mark">已选中</div>':""}
      <div class="card-head">
        <div>
          <div class="badges">
            <span class="badge source">收藏更新</span>
            ${update.latest_release_tag?`<span class="badge source">${h(update.latest_release_tag)}</span>`:""}
          </div>
          <a class="title" href="${h(update.url)}" target="_blank" rel="noopener" data-external-url="${h(update.url)}">${h(update.full_name)}</a>
        </div>
        <div class="meta meta-rank">${h(update.checked_at||"最近检查时间未知")}</div>
      </div>
      <div class="card-body">
        ${changeBadges?`<div class="badges">${changeBadges}</div>`:""}
        <div class="desc">${h(summary)}</div>
        <div class="meta-line">
          <span class="meta-pill"><strong>Stars</strong><span>${update.stars||0}</span></span>
          <span class="meta-pill"><strong>Forks</strong><span>${update.forks||0}</span></span>
          <span class="meta-pill"><strong>Pushed</strong><span>${h(update.pushed_at||"未知")}</span></span>
        </div>
        <div class="states">
          <button class="action" onclick='analyzeRepo(${JSON.stringify(update.url)})'>ChatGPT</button>
          <button class="action" onclick='openDetailFromRecord(${JSON.stringify(update.full_name)}, ${JSON.stringify(update.url)})'>详情</button>
        </div>
      </div>
    </article>`;
  }).join("");
}
function render(){
  cleanupSelected();
  ensureValidPanel();
  const isUpdatePanel=panel===UPDATE_PANEL_KEY;
  document.getElementById("note").textContent=currentNote;
  const languages=[...new Set((INITIAL.periods||[]).flatMap(period=>current(period.key).map(repo=>repo.language).filter(Boolean)))].sort((a,b)=>String(a).localeCompare(String(b),"zh-Hans-CN"));
  const languageNode=document.getElementById("language");
  languageNode.innerHTML='<option value="">全部语言</option>'+languages.map(language=>`<option value="${h(language)}">${h(language)}</option>`).join("");
  languageNode.value=languages.includes(languageFilter)?languageFilter:"";
  languageFilter=languageNode.value;
  languageNode.disabled=isUpdatePanel;
  document.getElementById("state-filter").disabled=isUpdatePanel;
  document.getElementById("tabs").innerHTML=tabsData().map(tab=>`<button class="tab ${tab.key===panel?"active":""}" onclick='setPanel(${JSON.stringify(tab.key)})'>${h(tab.label)} <span class="tab-count">${tab.count}</span></button>`).join("");
  const repos=visibleRepos();
  const updates=visibleUpdates();
  const selected=selectedCount();
  document.getElementById("visible-count").textContent=isUpdatePanel?updates.length:repos.length;
  document.getElementById("visible-label").textContent=isUpdatePanel?" 条更新":" 个仓库";
  document.getElementById("selected-count").textContent=selected;
  document.getElementById("selection-title").textContent=selected?`已选 ${selected} 个条目，可批量分析、改状态或双仓库对比`:"Selected Repositories";
  document.getElementById("batch-actions-row").classList.toggle("show",selected>0);
  document.getElementById("cards").innerHTML=isUpdatePanel?renderUpdateCards(updates):renderRepoCards(repos);
}
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
async function openCompareSelected(){
  const repos=selectedRepos();
  if(repos.length!==2){toast("请先选中 2 个仓库再对比");return;}
  document.getElementById("compare-body").innerHTML='<div class="empty">正在拉取对比数据...</div>';
  document.getElementById("compare-modal").classList.add("show");
  try{
    const [repoA,repoB]=repos;
    const [detailA,detailB]=await Promise.all([fetchRepoDetails(repoA),fetchRepoDetails(repoB)]);
    comparePrompt=buildComparePrompt(repoA,repoB,detailA,detailB);
    document.getElementById("compare-body").innerHTML=`<div class="notice">对比抽屉会把两个仓库按同一组维度并排展开，方便从语言、活跃度、README 摘要与项目定位几个层面做快速判断。</div><div class="panel-actions"><button class="action primary" onclick="analyzeCompare()">ChatGPT 对比</button></div><div class="compare-grid">${renderCompareCard(repoA,detailA)}${renderCompareCard(repoB,detailB)}</div>`;
  }catch(error){
    comparePrompt="";
    document.getElementById("compare-body").innerHTML=`<div class="empty">${h(error.message||"对比数据加载失败")}</div>`;
  }
}
function renderCompareCard(repo,detail){
  return `<article class="compare-card">
    <div class="badges">
      <span class="badge ${gainBadgeClass(repo)}">${h(gainLabel(repo))}</span>
      <span class="badge source">${h(repo.source_label||"GitHub 来源")}</span>
    </div>
    <div class="title">${h(repo.full_name)}</div>
    <div class="desc">${h(detail.description||detail.description_raw||repo.description||repo.description_raw||"暂无描述")}</div>
    <div class="detail-grid">
      <div class="detail-item"><strong>语言</strong><span>${h(repo.language||"未知语言")}</span></div>
      <div class="detail-item"><strong>License</strong><span>${h(detail.license||"未标注")}</span></div>
      <div class="detail-item"><strong>Stars</strong><span>${detail.stars||repo.stars||0}</span></div>
      <div class="detail-item"><strong>Forks</strong><span>${detail.forks||repo.forks||0}</span></div>
      <div class="detail-item"><strong>最近推送</strong><span>${h(detail.pushed_at||"未知")}</span></div>
      <div class="detail-item"><strong>Open Issues</strong><span>${detail.open_issues||0}</span></div>
    </div>
    <div class="desc muted">${h(detail.readme_summary||detail.readme_summary_raw||"暂无 README 摘要")}</div>
    <div class="panel-actions">
      <a class="action" href="${h(repo.url)}" target="_blank" rel="noopener" data-external-url="${h(repo.url)}">打开 GitHub</a>
    </div>
  </article>`;
}
async function analyzeCompare(){if(!comparePrompt){toast("当前没有可分析的对比内容");return;}await openChatGPTPrompts([comparePrompt]);}
async function toggleState(key,url){const repo=repoByUrl(url);if(!repo) return;const resp=await fetch("/api/state",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({state:key,enabled:!((userState[key]||[]).includes(url)),repo})});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||"保存失败");return;}userState=data.user_state;render();}
async function batchSetState(stateKey){const repos=selectedRepos();if(!repos.length){toast("请先选中仓库再批量操作");return;}let lastState=null;for(const repo of repos){const resp=await fetch("/api/state",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({state:stateKey,enabled:true,repo})});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||"批量操作失败");return;}if(data.user_state) lastState=data.user_state;}if(lastState) userState=lastState;render();const label=(INITIAL.states||[]).find(state=>state.key===stateKey)?.label||stateKey;toast(`已将 ${repos.length} 个仓库加入“${label}”`);}
async function clearFavoriteUpdates(){if(!(userState.favorite_updates||[]).length){toast("当前没有收藏更新记录");return;}if(!window.confirm("确认清空收藏更新记录吗？")) return;const resp=await fetch("/api/favorite-updates/clear",{method:"POST"});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||"清空失败");return;}userState=data.user_state;render();toast(data.message||"已清空收藏更新记录");}
async function refreshNow(){const resp=await fetch("/api/refresh",{method:"POST"});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||"刷新失败");return;}currentNote=data.message||"已开始后台刷新。";render();poll();}
function poll(){clearInterval(window.__pollTimer);window.__pollTimer=setInterval(async()=>{const resp=await fetch("/api/status?ts="+Date.now(),{cache:"no-store"});const data=await resp.json();currentNote=data.refreshing?"后台刷新中...":(data.error||"已显示最新数据");document.getElementById("note").textContent=currentNote;if(!data.refreshing){clearInterval(window.__pollTimer);location.reload();}},1500);}
async function hideToTray(){const resp=await fetch("/api/window/hide",{method:"POST"});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||data.message||"隐藏到托盘失败");return;}toast(data.message||"已隐藏到系统托盘");setTimeout(()=>window.close(),150);}
async function exitApp(){if(!window.confirm("确认直接退出 GitSonar 吗？")) return;const resp=await fetch("/api/window/exit",{method:"POST"});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||data.message||"退出程序失败");return;}toast(data.message||"正在退出程序");setTimeout(()=>window.close(),150);}
async function openSettings(){try{const resp=await fetch("/api/settings",{cache:"no-store"});const data=await resp.json();if(resp.ok) settings=data;}catch(_err){}document.getElementById("setting-token").value=settings.github_token||"";document.getElementById("setting-proxy").value=settings.proxy||"";document.getElementById("setting-refresh-hours").value=settings.refresh_hours||1;document.getElementById("setting-result-limit").value=settings.result_limit||25;document.getElementById("setting-port").value=settings.port||8080;document.getElementById("setting-close-behavior").value=settings.close_behavior||"tray";document.getElementById("setting-auto-start").checked=!!settings.auto_start;document.getElementById("settings-runtime-hint").textContent=`当前生效端口 ${settings.effective_port||settings.port||8080} · 当前代理 ${settings.effective_proxy||"未启用"} · 当前关闭行为 ${closeBehaviorLabel(settings.close_behavior)} · 程序不提供 VPN${settings.restart_required?" · 修改端口后需重启生效":""}`;document.getElementById("settings-modal").classList.add("show");}
function closeSettings(){document.getElementById("settings-modal").classList.remove("show");}
async function saveSettings(){const payload={github_token:document.getElementById("setting-token").value,proxy:document.getElementById("setting-proxy").value,refresh_hours:Number(document.getElementById("setting-refresh-hours").value||1),result_limit:Number(document.getElementById("setting-result-limit").value||25),port:Number(document.getElementById("setting-port").value||8080),close_behavior:document.getElementById("setting-close-behavior").value,auto_start:document.getElementById("setting-auto-start").checked,default_sort:sortPrimary};const resp=await fetch("/api/settings",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});const data=await resp.json();if(!resp.ok||!data.ok){toast(data.error||"保存失败");return;}settings=data.settings;toast(data.message||"设置已保存");closeSettings();}
"""
HTML_TEMPLATE_PART_3 = """async function openDetail(owner,name,label){document.getElementById("detail-modal").classList.add("show");document.getElementById("detail-title").textContent=label;document.getElementById("detail-body").innerHTML='<div class="empty">正在拉取仓库详情...</div>';try{const detail=await fetchRepoDetails({owner,name});const topics=Array.isArray(detail.topics)?detail.topics.filter(Boolean):[];document.getElementById("detail-body").innerHTML=`<div class="badges"><span class="badge source">${h(detail.license||"未标注 License")}</span><span class="badge source">${h(detail.default_branch||"未知分支")}</span>${detail.homepage?`<a class="badge source" href="${h(detail.homepage)}" target="_blank" rel="noopener" data-external-url="${h(detail.homepage)}">Homepage</a>`:""}</div><div class="desc">${h(detail.description||detail.description_raw||"暂无简介")}</div><div class="meta-line"><span class="meta-pill"><strong>Stars</strong><span>${detail.stars||0}</span></span><span class="meta-pill"><strong>Forks</strong><span>${detail.forks||0}</span></span><span class="meta-pill"><strong>Watchers</strong><span>${detail.watchers||0}</span></span><span class="meta-pill"><strong>Issues</strong><span>${detail.open_issues||0}</span></span></div><div class="detail-grid"><div class="detail-item"><strong>仓库</strong><span>${h(detail.full_name||label)}</span></div><div class="detail-item"><strong>最近推送</strong><span>${h(detail.pushed_at||"未知")}</span></div><div class="detail-item"><strong>最后更新</strong><span>${h(detail.updated_at||"未知")}</span></div><div class="detail-item"><strong>默认分支</strong><span>${h(detail.default_branch||"未知")}</span></div><div class="detail-item"><strong>License</strong><span>${h(detail.license||"未标注")}</span></div><div class="detail-item"><strong>主页</strong><span>${detail.homepage?`<a class="link-inline" href="${h(detail.homepage)}" target="_blank" rel="noopener" data-external-url="${h(detail.homepage)}">${h(detail.homepage)}</a>`:"未填写"}</span></div></div><div class="desc muted">${h(detail.readme_summary||detail.readme_summary_raw||"暂无 README 摘要")}</div>${topics.length?`<div class="topic-list">${topics.map(topic=>`<span class="topic">${h(topic)}</span>`).join("")}</div>`:""}<div class="panel-actions"><a class="action primary" href="${h(detail.html_url||"#")}" target="_blank" rel="noopener" data-external-url="${h(detail.html_url||"#")}">打开 GitHub</a></div>`;}catch(error){document.getElementById("detail-body").innerHTML=`<div class="empty">${h(error.message||"详情获取失败")}</div>`;}}
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
